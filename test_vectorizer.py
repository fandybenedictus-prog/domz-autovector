import os
import django
import sys
from pathlib import Path

# Setup Django Environment to read settings
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autovektor.settings')
django.setup()

from core.services import process_image_to_vector

def test_api():
    input_image = BASE_DIR / "media" / "uploads" / "ChatGPT_Image_Feb_24_2026_02_05_34_PM.png"
    output_svg = BASE_DIR / "test_out_vectorizer.svg"
    
    if not input_image.exists():
        print(f"Error: Test image not found at {input_image}")
        print("Please provide a valid image path.")
        return

    print(f"Testing Vectorizer.ai API with image: {input_image.name}...")
    try:
        process_image_to_vector(str(input_image), str(output_svg), num_colors=5)
        print(f"Success! SVG saved to: {output_svg}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_api()
