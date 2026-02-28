"""
services.py – Mesin Tracer (Jantung Aplikasi AutoVektor)

Fungsi utama: process_image_to_vector(input_path, output_path)

Pipeline:
  1. Buka & Upscale 2x  → lekukan lebih jelas untuk tracer
  2. Denoise            → hilangkan noise/bintik pada JPG kualitas rendah
  3. Simpan ke temp     → file sementara sebelum di-trace
  4. Vectorize          → konversi ke SVG via vtracer
  5. Cleanup            → hapus file temp
"""

import uuid
import os
import cv2
import vtracer


import numpy as np


def process_image_to_vector(input_path: str, output_path: str, num_colors: int = None) -> None:
    """
    Konversi gambar raster (JPG/PNG) menjadi file SVG berkualitas tinggi.

    Args:
        input_path  : Path absolut ke gambar sumber (JPG atau PNG).
        output_path : Path absolut untuk menyimpan hasil SVG.

    Raises:
        ValueError : Jika gambar tidak bisa dibaca oleh OpenCV.
        RuntimeError: Jika vtracer gagal melakukan konversi.
    """

    # ------------------------------------------------------------------
    # STEP 1 – PRE-PROCESSING
    # Memperbesar dimensi agar lekukan lebih tegas, atau mengkuantisasi warna
    # ------------------------------------------------------------------
    img = cv2.imread(input_path)
    if img is None:
        raise ValueError(f"Tidak dapat membuka gambar: {input_path}")

    h, w = img.shape[:2]

    # OPTIONAL K-MEANS COLOR QUANTIZATION
    if num_colors is not None and num_colors > 0:
        # STEP 1: Upscale 2x dengan LANCZOS (Penting!)
        # K-Means butuh area gradasi (anti-aliasing) di tepian warna agar saat dikuantisasi
        # tepiannya membentuk outline yang saling menimpa rapat (tidak memotong tajam)
        img_up = cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_LANCZOS4)
        
        # STEP 2: Denoise pada gambar yang sudah di-upscale
        img_denoised = cv2.fastNlMeansDenoisingColored(img_up, None, 10, 10, 7, 21)
        
        # STEP 3: K-Means Color Quantization
        Z = img_denoised.reshape((-1, 3))
        Z = np.float32(Z)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        ret, label, center = cv2.kmeans(Z, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        center = np.uint8(center)
        res = center[label.flatten()]
        img_quantized = res.reshape((img_up.shape))
        
        # STEP 4: Ratakan sisa-sisa bercak bekas pemotongan warna K-Means 
        # dengan Bilateral (meratakan interior) + Median Blur (membulatkan ujung)
        img_smoothed = cv2.bilateralFilter(img_quantized, 9, 75, 75)
        img_processed = cv2.medianBlur(img_smoothed, 15)

        # Threshold vtracer disesuaikan agar tidak memotong detail
        ct, fs, ld, len_th = 45, 10, 32, 10.0
    else:
        # JIKA TANPA K-MEANS (Standard Smoothing)
        # Upscale 2x Lanczos untuk menambah resolusi, agar lekuk lebih detail
        img_upscaled = cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_LANCZOS4)
        img_denoised = cv2.fastNlMeansDenoisingColored(img_upscaled, None, 10, 10, 7, 21)
        img_smoothed = cv2.bilateralFilter(img_denoised, 9, 75, 75)
        # Median blur sedikit (k=7) untuk meratakan pinggiran
        img_processed = cv2.medianBlur(img_smoothed, 7)

        # Gunakan threshold vtracer standar yang terbukti mulus (seperti di test_vtracer.py)
        ct, fs, ld, len_th = 45, 10, 32, 10.0


    # ------------------------------------------------------------------
    # STEP 3 – SIMPAN KE FILE TEMP
    # Menggunakan UUID agar tidak ada konflik jika ada proses paralel.
    # ------------------------------------------------------------------
    temp_filename = f"temp_{uuid.uuid4().hex}.png"
    # Simpan ke direktori yang sama dengan output agar mudah di-cleanup
    temp_dir = os.path.dirname(output_path) or "."
    temp_path = os.path.join(temp_dir, temp_filename)

    # Simpan sebagai PNG (lossless) agar kualitas maksimal saat di-trace
    cv2.imwrite(temp_path, img_processed)

    # ------------------------------------------------------------------
    # Jalankan vtracer dengan parameter dinamis
    # ------------------------------------------------------------------
    try:
        vtracer.convert_image_to_svg_py(
            temp_path,
            output_path,
            colormode='color',
            hierarchical='stacked', 
            mode='spline', 
            filter_speckle=fs,         
            color_precision=6, 
            layer_difference=ld,      
            corner_threshold=ct,      
            length_threshold=len_th,     
            max_iterations=10, 
            splice_threshold=45, 
            path_precision=8 
        )
    except Exception as exc:
        raise RuntimeError(f"vtracer gagal melakukan konversi: {exc}") from exc
    finally:
        # ------------------------------------------------------------------
        # STEP 5 – CLEANUP
        # Hapus file temp meski terjadi error, agar tidak menumpuk di disk.
        # ------------------------------------------------------------------
        if os.path.exists(temp_path):
            os.remove(temp_path)


def generate_quantized_preview(input_path: str, output_path: str, num_colors: int) -> None:
    """
    Menghasilkan gambar raster WebP/JPG yang disederhanakan warnanya menggunakan K-Means.
    Digunakan untuk preview real-time di Editor sebelum dirender ke SVG.
    """
    img = cv2.imread(input_path)
    if img is None:
        raise ValueError(f"Tidak dapat membuka gambar: {input_path}")

    if num_colors > 0:
        Z = img.reshape((-1, 3))
        Z = np.float32(Z)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        ret, label, center = cv2.kmeans(Z, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        center = np.uint8(center)
        res = center[label.flatten()]
        img = res.reshape((img.shape))

    # Downscale slightly for faster preview rendering over network, max dimension 1000px
    h, w = img.shape[:2]
    max_dim = 1000
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    cv2.imwrite(output_path, img)


def extract_dominant_colors(input_path: str, num_colors: int = 16) -> list:
    """
    Mengekstrak warna paling dominan dari gambar menggunakan K-Means secara cepat (downscaled).
    Digunakan untuk merender warna background pada tombol preset Palet di halaman Editor.
    Kembalian: list string HEX color, misal: ['#ffffff', '#000000', ...]
    """
    img = cv2.imread(input_path)
    if img is None:
        return []

    # BGR to RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Downscale drastis agar K-Means berjalan super cepat (instant)
    max_dim = 150
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    Z = img.reshape((-1, 3))
    Z = np.float32(Z)
    
    # Hitung jumlah warna unik, untuk jaga-jaga kalau gambar sangat solid/simpel
    unique_pixels = len(np.unique(Z, axis=0))
    k = min(num_colors, unique_pixels)
    if k == 0:
        return []

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    ret, label, center = cv2.kmeans(Z, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    # Hitung seberapa sering setiap cluster muncul (Sorting dari dominan ke minor)
    counts = np.bincount(label.flatten())
    sorted_centers = [center[i] for i in np.argsort(counts)[::-1]]
    
    hex_colors = []
    for c in sorted_centers:
        hex_colors.append('#{:02x}{:02x}{:02x}'.format(int(c[0]), int(c[1]), int(c[2])))
        
    # Jika gagal mencapai jumlah num_colors target, pad dengan warna terakhir atau default
    while len(hex_colors) < num_colors:
        hex_colors.append(hex_colors[-1] if hex_colors else '#374151')

    return hex_colors
