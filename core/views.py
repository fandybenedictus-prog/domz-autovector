"""
Views – AutoVektor Core App

Endpoints:
  /                   → home (landing page)
  /register/          → register_view
  /login/             → login_view  (custom, bukan auth default)
  /logout/            → logout_view
  /studio/            → studio_view  (upload & proses gambar)
  /result/<id>/       → result_view  (preview before/after)
  /download/<id>/     → download_view (cek saldo, potong, serve SVG)
  /topup/             → topup_view  (form top-up)
  /topup/confirm/     → topup_confirm_view
  /history/           → history_view (daftar TraceJob milik user)
"""

import os
from pathlib import Path

import os
from pathlib import Path

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404, JsonResponse

from .forms import RegisterForm, TopUpForm, TraceUploadForm
from .models import TopUpTransaction, TraceJob
from .services import process_image_to_vector, generate_quantized_preview, extract_dominant_colors


# ---------------------------------------------------------------------------
# Halaman Utama
# ---------------------------------------------------------------------------
def home(request):
    """Landing page – redirect ke studio jika sudah login."""
    if request.user.is_authenticated:
        return redirect('studio')

    steps = [
        {'icon': '📁', 'title': 'Upload Gambar',     'desc': 'Upload JPG, PNG, atau WebP dari perangkat Anda kapan saja.'},
        {'icon': '⚙️', 'title': 'Proses Otomatis',   'desc': 'Mesin AI kami membersihkan noise & mengkonversi ke kurva SVG halus.'},
        {'icon': '👁️', 'title': 'Preview Hasil',      'desc': 'Lihat perbandingan sebelum & sesudah mengonversi gambar.'},
        {'icon': '⬇️', 'title': 'Download SVG',       'desc': 'Download file SVG asli sebesar 100% GRATIS selama masa peluncuran Beta.'},
    ]
    features = [
        'Konversi warna penuh (bukan hitam-putih saja)',
        'Kurva bezier halus, bukan polygon kasar',
        'Preprocessing OpenCV: upscale + denoise',
        'File SVG siap pakai di Illustrator / Inkscape',
        'Riwayat konversi tersimpan permanen',
        'Saldo tidak pernah hangus',
    ]
    return render(request, 'core/home.html', {'steps': steps, 'features': features})


# ---------------------------------------------------------------------------
# Autentikasi
# ---------------------------------------------------------------------------
def register_view(request):
    if request.user.is_authenticated:
        return redirect('studio')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        # Auto-login setelah registrasi berhasil
        login(request, user)
        messages.success(request, f'Selamat datang, {user.username}! Akun berhasil dibuat.')
        return redirect('studio')

    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('studio')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Kembalikan ke halaman yang dicoba diakses sebelumnya (jika ada)
            next_url = request.GET.get('next', 'studio')
            return redirect(next_url)
        else:
            messages.error(request, 'Username atau password salah.')

    return render(request, 'core/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


# ---------------------------------------------------------------------------
# Studio – Upload & Proses Gambar
# ---------------------------------------------------------------------------
@login_required
def studio_view(request):
    """
    GET  : Tampilkan form upload.
    POST : Terima gambar, simpan TraceJob, lalu redirect ke halaman Editor.
    """
    form = TraceUploadForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        gambar_file = form.cleaned_data['gambar']

        # 1. Buat TraceJob dan simpan gambar asli ke disk
        job = TraceJob.objects.create(
            user=request.user,
            gambar_asli=gambar_file,
        )

        # SEKARANG KITA TIDAK LANGSUNG VEKTORISASI
        # Redirect ke Editor Interaktif
        return redirect('editor', job_id=job.pk)

    return render(request, 'core/studio.html', {'form': form})


# ---------------------------------------------------------------------------
# Editor – Interaktif K-Means Color Choice
# ---------------------------------------------------------------------------
@login_required
def editor_view(request, job_id):
    """
    Menampilkan UI untuk mencoba berbagai preset jumlah warna.
    """
    job = get_object_or_404(TraceJob, pk=job_id, user=request.user)
    
    # Check jika user reload halaman atau akses ulang job yang sudah divisualisasi
    if job.file_vektor:
        return redirect('result', job_id=job.pk)
        
    try:
        # Ekstrak 50 warna paling dominan dari gambar menggunakan K-Means untuk list preview
        palette = extract_dominant_colors(job.gambar_asli.path, 50)
    except Exception:
        palette = []
        
    context = {
        'job': job,
        'palette': palette,
    }
    return render(request, 'core/editor.html', context)


@login_required
def preview_colors_api(request, job_id):
    """
    Endpoint AJAX untuk menghasilkan gambar raster K-Means sementara
    berdasarkan jumlah warna yang di-request user.
    """
    job = get_object_or_404(TraceJob, pk=job_id, user=request.user)
    num_colors = int(request.GET.get('colors', 0))
    
    if num_colors < 2 or num_colors > 50:
        return JsonResponse({'error': 'Jumlah warna tidak valid'}, status=400)
        
    try:
        from django.conf import settings
        input_path = job.gambar_asli.path
        
        # Buat temporary folder if not exists
        temp_dir = Path(settings.MEDIA_ROOT) / 'temp_previews'
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Nama file hash cache supaya kalau user klik 3 warna 2 kali, kita gak run ulang tapi bisa ngeload file sama. Tapi untuk simplifikasi:
        preview_filename = f"preview_{job.pk}_c{num_colors}.jpg"
        output_path = temp_dir / preview_filename
        
        if not output_path.exists():
            generate_quantized_preview(input_path, str(output_path), num_colors)
            
        preview_url = f"{settings.MEDIA_URL}temp_previews/{preview_filename}"
        return JsonResponse({'preview_url': preview_url})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def vectorize_action(request, job_id):
    """
    Finalize proses vtracer berdasarkan warna pilihan terakhir.
    """
    if request.method != 'POST':
        return redirect('studio')
        
    job = get_object_or_404(TraceJob, pk=job_id, user=request.user)
    num_colors = int(request.POST.get('colors', 0))
    
    if num_colors < 2:
        num_colors = None # Bypass quantization (bawaan lama)

    from django.conf import settings
    output_filename = f"job_{job.pk}.svg"
    output_dir      = Path(settings.MEDIA_ROOT) / 'vektor_output'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / output_filename)

    try:
        input_path = job.gambar_asli.path
        # PROSES INI MEMAKAN WAKTU
        process_image_to_vector(input_path, output_path, num_colors=num_colors)

        job.file_vektor = f"vektor_output/{output_filename}"
        job.save()

        messages.success(request, 'Gambar berhasil dikonversi dengan palet khusus! Silakan preview dan download SVG-nya.')
        return redirect('result', job_id=job.pk)

    except Exception as exc:
        job.delete()
        messages.error(request, f'Gagal memproses gambar: {exc}')
        return redirect('studio')


# ---------------------------------------------------------------------------
# Result – Preview Before/After
# ---------------------------------------------------------------------------
@login_required
def result_view(request, job_id):
    """Tampilkan gambar asli (before) dan SVG preview (after) + tombol download."""
    job = get_object_or_404(TraceJob, pk=job_id, user=request.user)

    if not job.file_vektor:
        messages.error(request, 'File vektor belum tersedia untuk job ini.')
        return redirect('studio')

    context = {
        'job':    job,
        'saldo':  request.user.profile.saldo,
        'harga':  0,
        'cukup':  True, # Selalu cukup karena digratiskan
    }
    return render(request, 'core/result.html', context)


# ---------------------------------------------------------------------------
# Download – Potong Saldo & Serve File
# ---------------------------------------------------------------------------
@login_required
def download_view(request, job_id):
    """
    Alur download aman:
      1. Cek saldo user >= Rp2.000.
      2. Potong saldo, tandai is_paid=True (transaksi atomik sederhana).
      3. Serve file SVG menggunakan FileResponse (bukan URL publik langsung).

    Menggunakan direct FileResponse, bukan redirect ke /media/, agar file vektor
    tidak bisa diakses tanpa autentikasi hanya dengan URL-nya.
    """
    job = get_object_or_404(TraceJob, pk=job_id, user=request.user)

    if not job.file_vektor:
        raise Http404("File vektor tidak ditemukan.")

    profile = request.user.profile
    HARGA   = 2000

    # Jika sudah pernah dibayar, langsung serve ulang tanpa potong saldo lagi
    if job.is_paid:
        return _serve_svg(job)

    # Bypass Cek Saldo & Potongan (100% FREE BETA)
    # ------------------------------------------------------------------
    # if profile.saldo < HARGA:
    #     messages.error(...)
    #     return redirect('topup')
    #
    # profile.saldo -= HARGA
    # profile.save()
    # ------------------------------------------------------------------

    job.is_paid = True
    job.save()

    messages.success(request, 'Download berhasil! Aplikasi saat ini masih dalam masa Beta dan 100% Gratis.')
    return _serve_svg(job)


def _serve_svg(job: TraceJob) -> FileResponse:
    """Helper untuk men-serve file SVG sebagai attachment downloadan."""
    svg_path = job.file_vektor.path
    if not os.path.exists(svg_path):
        raise Http404("File SVG tidak ditemukan di server.")

    # Ambil nama file asli dari gambar asli sebagai nama unduhan
    original_name = Path(job.gambar_asli.name).stem
    download_name = f"{original_name}_vektor.svg"

    response = FileResponse(
        open(svg_path, 'rb'),
        content_type='image/svg+xml',
    )
    response['Content-Disposition'] = f'attachment; filename="{download_name}"'
    return response


# ---------------------------------------------------------------------------
# Top-Up Saldo
# ---------------------------------------------------------------------------
@login_required
def topup_view(request):
    form = TopUpForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        TopUpTransaction.objects.create(
            user           = request.user,
            nominal        = form.cleaned_data['nominal'],
            bukti_transfer = form.cleaned_data['bukti_transfer'],
        )
        return redirect('topup_confirm')

    context = {
        'form':  form,
        'saldo': request.user.profile.saldo,
        # Informasi rekening penerima (ganti dengan data asli Anda)
        'rekening': {
            'nama':   'AutoVektor Official',
            'bank':   'BCA',
            'nomor':  '1234567890',
        }
    }
    return render(request, 'core/topup.html', context)


@login_required
def topup_confirm_view(request):
    """Halaman konfirmasi bahwa bukti transfer sudah diterima."""
    return render(request, 'core/topup_confirm.html')


# ---------------------------------------------------------------------------
# History – Daftar job milik user
# ---------------------------------------------------------------------------
@login_required
def history_view(request):
    jobs  = TraceJob.objects.filter(user=request.user)
    context = {
        'jobs':  jobs,
        'saldo': request.user.profile.saldo,
    }
    return render(request, 'core/history.html', context)
