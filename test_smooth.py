import cv2
import vtracer
import numpy as np

def process_test(input_path, output_path, config_id):
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
    img = res.reshape((img.shape))
    
    h, w = img.shape[:2]

    if config_id == 1:
        # Config 1: Upscale -> Gaussian Blur -> Median Blur
        # Goal: Gaussian to create gradations on the staircases, then median to sharpen the curve slightly
        img_upscaled = cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_LANCZOS4)
        img_smooth = cv2.GaussianBlur(img_upscaled, (5, 5), 0)
        img_smooth = cv2.medianBlur(img_smooth, 7)
    elif config_id == 2:
        # Config 2: Upscale -> pyrMeanShiftFiltering
        img_upscaled = cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_LANCZOS4)
        img_smooth = cv2.pyrMeanShiftFiltering(img_upscaled, 10, 30)
    elif config_id == 3:
        # Config 3: Stronger Gaussian Blur -> Bilateral
        img_upscaled = cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_LANCZOS4)
        img_smooth = cv2.GaussianBlur(img_upscaled, (9, 9), 0)
        img_smooth = cv2.bilateralFilter(img_smooth, 9, 75, 75)
    elif config_id == 4:
        # Config 4: Gaussian Blur BEFORE upscale to antialias the staircases, then upscale
        img_smooth = cv2.GaussianBlur(img, (3, 3), 0)
        img_upscaled = cv2.resize(img_smooth, (w * 2, h * 2), interpolation=cv2.INTER_LANCZOS4)
        # minor cleanup
        img_smooth = cv2.fastNlMeansDenoisingColored(img_upscaled, None, 10, 10, 7, 21)
    else:
        return

    temp_path = f"temp_{config_id}.png"
    cv2.imwrite(temp_path, img_smooth)
    
    vtracer.convert_image_to_svg_py(
        temp_path,
        output_path,
        colormode='color',
        hierarchical='stacked', 
        mode='spline', 
        filter_speckle=10, 
        color_precision=6, 
        layer_difference=32,
        corner_threshold=45, 
        length_threshold=10.0, 
        max_iterations=10, 
        splice_threshold=45, 
        path_precision=8 
    )
    print(f"Done config {config_id}")

img_path = 'media/uploads/ChatGPT_Image_Feb_24_2026_02_05_34_PM.png'
process_test(img_path, 'out_config1.svg', 1)
process_test(img_path, 'out_config2.svg', 2)
process_test(img_path, 'out_config3.svg', 3)
process_test(img_path, 'out_config4.svg', 4)
