import cv2
import vtracer
import os

def test_trace(input_path, output_path):
    print(f"Reading {input_path}")
    img = cv2.imread(input_path)
    h, w = img.shape[:2]
    
    # 2x upscale
    print("Upscaling...")
    img_upscaled = cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_LANCZOS4)
    
    # Denoise (existing)
    print("Denoising...")
    img_denoised = cv2.fastNlMeansDenoisingColored(
        img_upscaled, None, 10, 10, 7, 21
    )

    # NEW: Bilateral Filter to flatten colors & keep main edges
    print("Bilateral filter...")
    img_smoothed = cv2.bilateralFilter(img_denoised, d=9, sigmaColor=75, sigmaSpace=75)
    
    # NEW: Median Blur to round off jagged edges
    print("Median blur...")
    img_smoothed = cv2.medianBlur(img_smoothed, 5)
    
    temp_path = "temp.png"
    cv2.imwrite(temp_path, img_smoothed)
    
    print("Tracing with vtracer...")
    vtracer.convert_image_to_svg_py(
        temp_path,
        output_path,
        colormode='color',
        hierarchical='stacked',
        mode='spline',
        filter_speckle=10,        # Increased from 4 for smoother look
        color_precision=6,        # Keep default
        layer_difference=32,      # Increased from 16 to merge slightly different colors
        corner_threshold=45,      # Decreased from 60 to allow more curves
        length_threshold=10.0,    # Increased from 4.0 to remove jaggy short segments
        max_iterations=10,
        splice_threshold=45,
    )
    print(f"Saved to {output_path}")

test_trace('media/uploads/ChatGPT_Image_Feb_24_2026_02_05_34_PM.png', 'test_out.svg')
