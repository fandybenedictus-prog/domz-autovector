import cv2
import numpy as np
import urllib.request
import os
import sys

# URL and path for a lightweight fast SR model (FSRCNN)
model_url = "https://github.com/Saafke/FSRCNN_Tensorflow/raw/master/models/FSRCNN_x3.pb"
model_path = "FSRCNN_x3.pb"

if not os.path.exists(model_path):
    print("Downloading FSRCNN model...")
    urllib.request.urlretrieve(model_url, model_path)
    print("Download complete.")
else:
    print("Model already exists.")

try:
    # Requires: pip install opencv-contrib-python
    from cv2 import dnn_superres
    sr = dnn_superres.DnnSuperResImpl_create()

    # Read image
    image = cv2.imread('media/uploads/ChatGPT_Image_Feb_24_2026_08_35_45_AM.png')
    if image is None:
        print("Could not load image.")
        sys.exit(1)
        
    print(f"Original shape: {image.shape}")

    # Read the desired model
    sr.readModel(model_path)

    # Set the desired model and scale to get correct pre- and post-processing
    sr.setModel("fsrcnn", 3)

    # Upscale the image
    print("Upscaling...")
    result = sr.upsample(image)
    print(f"Upscaled shape: {result.shape}")

    # Save
    cv2.imwrite("media/test_fsrcnn_x3.png", result)
    print("Saved as media/test_fsrcnn_x3.png")

except ImportError:
    print("Error: dnn_superres not found. Please run: pip install opencv-contrib-python")
except Exception as e:
    print(f"Error: {e}")
