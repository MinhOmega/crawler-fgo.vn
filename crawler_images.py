import os
import requests
import datetime
import sys
import json
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from io import BytesIO
from PIL import Image

def is_valid_image(content):
    try:
        # Try to open the content as an image using PIL
        img = Image.open(BytesIO(content))
        img.verify()  # Verify it's actually an image
        return True
    except Exception:
        return False

def download_image(code, base_folder):
    code_str = f"s{code}"
    url = f"https://fgo.vn/tai-anh-ve/?id={code_str}"
    
    try:
        # Make the request to get the image
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Get the full content
        content = response.content

        # Check if it's a valid image
        if not is_valid_image(content):
            print(f"Invalid image content for {url}")
            return False

        # Check if the response contains the error message
        if "Mã hình ảnh không đúng!" in response.text:
            print(f"Invalid image code for {url}")
            return False

        # Save the image to the corresponding folder
        image_path = os.path.join(base_folder, f"{code_str}.jpg")
        
        with open(image_path, "wb") as file:
            file.write(content)

        print(f"Downloaded and saved: {image_path}")
        return True

    except requests.RequestException as e:
        print(f"Failed to download {url}: {e}")
        return False
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return False

if __name__ == "__main__":
    # Dynamic range from arguments
    if len(sys.argv) != 3:
        print("Usage: python script.py <start_code> <end_code>")
        sys.exit(1)

    start_code = int(sys.argv[1])
    end_code = int(sys.argv[2])

    # Create the date-based folder
    today = datetime.datetime.now().strftime("%Y%m%d")
    output_dir = f"images_{today}_{start_code}_to_{end_code}"
    os.makedirs(output_dir, exist_ok=True)

    # Download images in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        codes = range(start_code, end_code + 1)
        # Pass output_dir to download_image using partial
        download_with_folder = partial(download_image, base_folder=output_dir)
        results = list(executor.map(download_with_folder, codes))

    # Print summary
    successful = sum(1 for r in results if r)
    print(f"Downloaded {successful} images out of {len(results)} attempts")
