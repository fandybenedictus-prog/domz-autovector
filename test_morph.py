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

    # Morphological tests to fix "wavy" and "jagged" by using solid geometry algorithms
    if config_id == '1':
        # Upscale 4x NN
        img_up = cv2.resize(img_kmeans, (w * 4, h * 4), interpolation=cv2.INTER_NEAREST)
        
        # Create circular kernel
        radius = 5
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1, radius * 2 + 1))
        
        # Morphological Close then Open to smooth boundaries mechanically without blurring
        img_morph = cv2.morphologyEx(img_up, cv2.MORPH_CLOSE, kernel)
        img_smooth = cv2.morphologyEx(img_morph, cv2.MORPH_OPEN, kernel)
        ct, fs, lt = 45, 10, 10.0
    elif config_id == '2':
        # Upscale 4x NN
        img_up = cv2.resize(img_kmeans, (w * 4, h * 4), interpolation=cv2.INTER_NEAREST)
        
        # Larger circular kernel
        radius = 9
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1, radius * 2 + 1))
        
        img_morph = cv2.morphologyEx(img_up, cv2.MORPH_CLOSE, kernel)
        img_smooth = cv2.morphologyEx(img_morph, cv2.MORPH_OPEN, kernel)
        ct, fs, lt = 60, 20, 15.0
    elif config_id == '3':
        # What if we upscale the original image FIRST (Lanczos), THEN K-Means?
        # The staircases might be much finer.
        img_up_orig = cv2.resize(img, (w * 4, h * 4), interpolation=cv2.INTER_LANCZOS4)
        img_up_orig = cv2.fastNlMeansDenoisingColored(img_up_orig, None, 10, 10, 7, 21)
        Z2 = img_up_orig.reshape((-1, 3))
        Z2 = np.float32(Z2)
        r, l, c = cv2.kmeans(Z2, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        c = np.uint8(c)
        res2 = c[l.flatten()]
        img_smooth = res2.reshape((img_up_orig.shape))
        
        # slight median blur just to kill single pixel noise from K-Means on high-res
        img_smooth = cv2.medianBlur(img_smooth, 7)
        ct, fs, lt = 45, 15, 15.0
    elif config_id == '4':
        # Config 3 but with Bilateral filter instead of Median
        img_up_orig = cv2.resize(img, (w * 3, h * 3), interpolation=cv2.INTER_LANCZOS4)
        Z2 = img_up_orig.reshape((-1, 3))
        Z2 = np.float32(Z2)
        r, l, c = cv2.kmeans(Z2, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        c = np.uint8(c)
        res2 = c[l.flatten()]
        img_smooth = res2.reshape((img_up_orig.shape))
        
        img_smooth = cv2.bilateralFilter(img_smooth, 9, 75, 75)
        ct, fs, lt = 60, 15, 15.0
    else:
        return

    temp_path = f"temp_morph_{config_id}.png"
    cv2.imwrite(temp_path, img_smooth)
    
    vtracer.convert_image_to_svg_py(
        temp_path,
        output_path,
        colormode='color',
        hierarchical='stacked', 
        mode='spline', 
        filter_speckle=fs, 
        color_precision=6, 
        layer_difference=16, 
        corner_threshold=ct, 
        length_threshold=lt, 
        max_iterations=10, 
        splice_threshold=45, 
        path_precision=8 
    )
    print(f"Done config {config_id}")

img_path = 'media/uploads/ChatGPT_Image_Feb_24_2026_02_05_34_PM.png'
generate(img_path, 'out_fix_1.svg', '1')
generate(img_path, 'out_fix_2.svg', '2')
generate(img_path, 'out_fix_3.svg', '3')
generate(img_path, 'out_fix_4.svg', '4')
