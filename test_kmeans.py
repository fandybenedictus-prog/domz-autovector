import os
import django
import cv2
import sys
import numpy as np
from pathlib import Path
import requests

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autovektor.settings')
django.setup()

from django.conf import settings

def test_kmeans_to_vectorizer():
    input_image = BASE_DIR / "media" / "uploads" / "ChatGPT_Image_Feb_24_2026_02_05_34_PM.png"
    output_svg = BASE_DIR / "test_out_kmeans.svg"
    temp_img = BASE_DIR / "temp_kmeans.png"
    
    num_colors = 5
    print(f"Applying K-Means with {num_colors} colors...")
    
    img = cv2.imread(str(input_image))
    h, w = img.shape[:2]
    
    # K-Means logic from old services.py
    img_upscaled = cv2.resize(img, (w * 3, h * 3), interpolation=cv2.INTER_LANCZOS4)
    Z = img_upscaled.reshape((-1, 3))
    Z = np.float32(Z)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    ret, label, center = cv2.kmeans(Z, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    center = np.uint8(center)
    res = center[label.flatten()]
    img_processed = res.reshape((img_upscaled.shape))
    img_processed = cv2.bilateralFilter(img_processed, 9, 75, 75)
    
    cv2.imwrite(str(temp_img), img_processed)
    print("Saved K-Means temp image. Sending to Vectorizer.ai...")
    
    api_key = settings.VECTORIZER_API_KEY
    api_secret = settings.VECTORIZER_API_SECRET
    
    with open(temp_img, 'rb') as f:
        # Also pass colors=5 just to be safe
        response = requests.post(
            'https://id.vectorizer.ai/api/v1/vectorize',
            files={'image': f},
            data={'colors': num_colors},
            auth=(api_key, api_secret)
        )
        
    if response.status_code == 200:
        with open(output_svg, 'wb') as out:
            out.write(response.content)
        print("Success! SVG saved.")
    else:
        print(f"Error {response.status_code}: {response.text}")
        
if __name__ == "__main__":
    test_kmeans_to_vectorizer()
