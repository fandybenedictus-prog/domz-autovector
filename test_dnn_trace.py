import cv2
import numpy as np
import vtracer

# Load AI Upscaled Image
img_upscaled = cv2.imread('media/test_fsrcnn_x3.png')
h, w = img_upscaled.shape[:2]

# K-Means on the AI upscaled image
num_colors = 16
Z = img_upscaled.reshape((-1, 3))
Z = np.float32(Z)
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
ret, label, center = cv2.kmeans(Z, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

center = np.uint8(center)
res = center[label.flatten()]
img_processed = res.reshape((img_upscaled.shape))

# Bilateral filter
img_processed = cv2.bilateralFilter(img_processed, 9, 75, 75)

temp_path_fsrcnn = "media/temp_fsrcnn.jpg"
cv2.imwrite(temp_path_fsrcnn, img_processed)

# Vectorize
out_path_fsrcnn = "media/out_fsrcnn_x3.svg"
vtracer.convert_image_to_svg_py(
    temp_path_fsrcnn,
    out_path_fsrcnn,
    colormode='color',
    hierarchical='stacked', 
    mode='spline', 
    filter_speckle=15, 
    color_precision=6, 
    layer_difference=16, 
    corner_threshold=60, 
    length_threshold=15.0, 
    max_iterations=10, 
    splice_threshold=45, 
    path_precision=8 
)
print("Saved FSRCNN tracing to", out_path_fsrcnn)
