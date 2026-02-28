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

    # Wavy Fix Hypothesis:
    # "Keriting" (Wavy) is caused by Median blur trying to round out 90-degree staircases. 
    # To get straight lines, we need Gaussian Blur or Lanczos interpolation to create a linear gradient 
    # between the steps, and then let vtracer's spline algorithm handle the gradient.
    if config_id == 'A':
        # Config A: Gaussian Blur directly on K-Means image, then Upscale Lanczos
        img_smooth = cv2.GaussianBlur(img_kmeans, (3, 3), 0)
        img_up = cv2.resize(img_smooth, (w * 3, h * 3), interpolation=cv2.INTER_LANCZOS4)
        ct, fs = 60, 20
    elif config_id == 'B':
        # Config B: Downscale slightly (to compress the stairs), then massive Upscale Lanczos
        img_down = cv2.resize(img_kmeans, (int(w * 0.75), int(h * 0.75)), interpolation=cv2.INTER_AREA)
        img_up = cv2.resize(img_down, (w * 3, h * 3), interpolation=cv2.INTER_LANCZOS4)
        ct, fs = 60, 20
    elif config_id == 'C':
        # Config C: No Blur at all! Just upscale LANCZOS so it interpolates, then let vtracer handle the gradients
        # Increase layer_difference so it merges the anti-aliased gradients
        img_up = cv2.resize(img_kmeans, (w * 4, h * 4), interpolation=cv2.INTER_LANCZOS4)
        ct, fs = 60, 30
    elif config_id == 'D':
        # Config D: Bilateral Filter (keeps edges sharp but removes stair noise) + Lanczos
        img_smooth = cv2.bilateralFilter(img_kmeans, 9, 75, 75)
        img_up = cv2.resize(img_smooth, (w * 3, h * 3), interpolation=cv2.INTER_LANCZOS4)
        ct, fs = 45, 20
    else:
        return

    temp_path = f"temp_wavy_{config_id}.png"
    cv2.imwrite(temp_path, img_up)
    
    vtracer.convert_image_to_svg_py(
        temp_path,
        output_path,
        colormode='color',
        hierarchical='stacked', 
        mode='spline', 
        filter_speckle=fs, 
        color_precision=6, 
        layer_difference=48, # High to merge gradients 
        corner_threshold=ct, 
        length_threshold=15.0, 
        max_iterations=10, # smooth out splines
        splice_threshold=45, 
        path_precision=8 
    )
    print(f"Done config {config_id}")

img_path = 'media/uploads/ChatGPT_Image_Feb_24_2026_02_05_34_PM.png'
generate(img_path, 'out_wavy_A.svg', 'A')
generate(img_path, 'out_wavy_B.svg', 'B')
generate(img_path, 'out_wavy_C.svg', 'C')
generate(img_path, 'out_wavy_D.svg', 'D')
