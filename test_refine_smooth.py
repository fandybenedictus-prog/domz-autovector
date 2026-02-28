import cv2
import vtracer
import numpy as np

def generate(input_path, output_path, config_id):
    img = cv2.imread(input_path)
    if img is None:
        print("Could not read image")
        return

    # K-Means simulation
    num_colors = 5
    Z = img.reshape((-1, 3))
    Z = np.float32(Z)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    ret, label, center = cv2.kmeans(Z, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    center = np.uint8(center)
    res = center[label.flatten()]
    img_kmeans = res.reshape((img.shape))
    
    h, w = img_kmeans.shape[:2]

    # Refinements based on out_smooth_1 (Upscale 2x NEAREST + Median)
    if config_id == 'A':
        # Config A: Median 11 (slightly less rounded than 15) + Bilateral to keep edges crisp
        img_up = cv2.resize(img_kmeans, (w * 2, h * 2), interpolation=cv2.INTER_NEAREST)
        img_smooth = cv2.medianBlur(img_up, 11)
        img_smooth = cv2.bilateralFilter(img_smooth, 9, 75, 75)
        ct, fs = 60, 10
    elif config_id == 'B':
        # Config B: Median 15 + Gaussian Blur 5x5 to smooth out the final jagged pixels 
        # before letting vtracer splice it, using stricter vtracer thresholds
        img_up = cv2.resize(img_kmeans, (w * 2, h * 2), interpolation=cv2.INTER_NEAREST)
        img_smooth = cv2.medianBlur(img_up, 15)
        img_smooth = cv2.GaussianBlur(img_smooth, (5, 5), 0)
        ct, fs = 45, 15
    elif config_id == 'C':
        # Config C: Upscale 3x Nearest + Median 21 (scales the Config 1 logic up slightly)
        img_up = cv2.resize(img_kmeans, (w * 3, h * 3), interpolation=cv2.INTER_NEAREST)
        img_smooth = cv2.medianBlur(img_up, 21)
        ct, fs = 60, 15
    elif config_id == 'D':
        # Config D: Median 15 but we change vtracer to ignore more corners and smooth things mechanically
        img_up = cv2.resize(img_kmeans, (w * 2, h * 2), interpolation=cv2.INTER_NEAREST)
        img_smooth = cv2.medianBlur(img_up, 15)
        ct, fs = 90, 20  # Try corner_threshold 90 to force curves
    else:
        return

    temp_path = f"temp_refine_{config_id}.png"
    cv2.imwrite(temp_path, img_smooth)
    
    vtracer.convert_image_to_svg_py(
        temp_path,
        output_path,
        colormode='color',
        hierarchical='stacked', 
        mode='spline', 
        filter_speckle=fs, 
        color_precision=6, 
        layer_difference=32,
        corner_threshold=ct, 
        length_threshold=10.0, 
        max_iterations=10, 
        splice_threshold=45, 
        path_precision=8 
    )
    print(f"Done config {config_id}")

img_path = 'media/uploads/ChatGPT_Image_Feb_24_2026_02_05_34_PM.png'
generate(img_path, 'out_refine_A.svg', 'A')
generate(img_path, 'out_refine_B.svg', 'B')
generate(img_path, 'out_refine_C.svg', 'C')
generate(img_path, 'out_refine_D.svg', 'D')
