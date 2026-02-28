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

    # Extreme Smoothing Hypothesis tests:
    if config_id == 1:
        # Config 1: Upscale 2x NEAREST (preserve stairs), then Median (15).
        img_up = cv2.resize(img_kmeans, (w * 2, h * 2), interpolation=cv2.INTER_NEAREST)
        img_smooth = cv2.medianBlur(img_up, 15)
        ct = 60
        fs = 10
    elif config_id == 2:
        # Config 2: Upscale 4x NEAREST, then massive Median Blur (31).
        img_up = cv2.resize(img_kmeans, (w * 4, h * 4), interpolation=cv2.INTER_NEAREST)
        img_smooth = cv2.medianBlur(img_up, 31)
        ct = 60
        fs = 15
    elif config_id == 3:
        # Config 3: Upscale 4x CUBIC, then Median Blur (31).
        # Cubic introduces mini gradients, median snaps them. Wait, Bilateral is better here?
        img_up = cv2.resize(img_kmeans, (w * 4, h * 4), interpolation=cv2.INTER_CUBIC)
        img_smooth = cv2.medianBlur(img_up, 31)
        ct = 90 # High corner threshold so potrace treats corners as curves
        fs = 20
    elif config_id == 4:
        # Config 4: Upscale 2x CUBIC, slight blur, let vtracer do EVERYTHING with extreme params
        img_up = cv2.resize(img_kmeans, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
        img_smooth = cv2.GaussianBlur(img_up, (5, 5), 0)
        ct = 1   # Try very low corner_threshold? To see if it smooths or sharpens
        fs = 20
    else:
        return

    temp_path = f"temp_smooth_{config_id}.png"
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
generate(img_path, 'out_smooth_1.svg', 1)
generate(img_path, 'out_smooth_2.svg', 2)
generate(img_path, 'out_smooth_3.svg', 3)
generate(img_path, 'out_smooth_4.svg', 4)
