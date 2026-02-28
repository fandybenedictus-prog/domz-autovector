import cv2
import vtracer
import numpy as np

def generate(input_path, output_path, use_fix=False):
    img = cv2.imread(input_path)
    h, w = img.shape[:2]

    num_colors = 5
    # KMEANS
    Z = img.reshape((-1, 3))
    Z = np.float32(Z)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    ret, label, center = cv2.kmeans(Z, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    center = np.uint8(center)
    res = center[label.flatten()]
    img = res.reshape((img.shape))

    if use_fix:
        # UPSCALE THEN BLUR
        img_upscaled = cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_LANCZOS4)
        
        # blur or median blur to smooth out the jagged k-means boundaries
        img_smoothed = cv2.medianBlur(img_upscaled, 7)
        img_processed = cv2.fastNlMeansDenoisingColored(img_smoothed, None, 10, 10, 7, 21)
    else:
        img_upscaled = cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_LANCZOS4)
        img_processed = cv2.fastNlMeansDenoisingColored(img_upscaled, None, h=3, hColor=3, templateWindowSize=7, searchWindowSize=21)

    temp_path = "temp2.png" if use_fix else "temp1.png"
    cv2.imwrite(temp_path, img_processed)

    vtracer.convert_image_to_svg_py(
        temp_path,
        output_path,
        colormode='color',
        hierarchical='stacked', 
        mode='spline', 
        filter_speckle=4, 
        color_precision=6,
        layer_difference=16,
        corner_threshold=60, 
        length_threshold=4.5, 
        max_iterations=10, 
        splice_threshold=45, 
        path_precision=8 
    )

generate('media/uploads/ChatGPT_Image_Feb_24_2026_02_05_34_PM.png', 'out1.svg', use_fix=False)
generate('media/uploads/ChatGPT_Image_Feb_24_2026_02_05_34_PM.png', 'out2.svg', use_fix=True)
