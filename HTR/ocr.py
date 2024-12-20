import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cv2
import numpy as np
from PIL import Image
import pytesseract
import argparse
from datetime import datetime

def detect_blue_ink(image):
    """Detect blue ink in the image."""
    # Convert to HSV color space
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Define blue color range in HSV
    lower_blue = np.array([90, 95, 50])
    upper_blue = np.array([120, 255, 255])
    
    # Create mask to detect blue color
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    cv2.imwrite('bluee.png', mask)
    
    # Apply morphological operations to improve mask
    kernel = np.ones((3,3),np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    cv2.imwrite('bluemask.png', mask)
    
    return mask

def preprocess_image(image_path):
    """Load and preprocess the image for better OCR accuracy."""
    try:
        # Read the image using OpenCV
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Image at {image_path} could not be loaded.")
        
        h,w = img.shape[:2]
        img = img[int(h*.19):(h//2)-int(h*.1), :w//2]


        # Detect blue ink
        blue_mask = detect_blue_ink(img)
        
        # Extract blue ink regions
        blue_ink = cv2.bitwise_and(img, img, mask=blue_mask)
        cv2.imwrite('blue.png', blue_ink)
        
        # Convert to grayscale
        gray = cv2.cvtColor(blue_ink, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 200, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 7, 2
        )

        new_size = (1274,737)
        
        thresh = cv2.resize(thresh, new_size)
        
        return thresh
        
    except Exception as e:
        print(f"Error preprocessing image: {str(e)}")
        return None

def resize_image(image, scale_factor=.01):
    """Resize the image to improve OCR accuracy."""
    try:
        height, width = image.shape
        new_size = int(width * scale_factor, height * scale_factor)
        resized_img = cv2.resize(image, new_size, interpolation=cv2.INTER_LINEAR)

        return resized_img
    except Exception as e:
        print(f"Error in resize_image: {e}")
        return image

def ocr_image(image):
    """Perform OCR on the preprocessed image."""
    try:
        pil_img = Image.fromarray(image)

        # Custom configuration for tesseract (LSTM OCR engine, automatic page segmentation)
        custom_config = r'-l eng+fil+spa+eng_handwritten --psm 6 --oem 3'

        # Perform OCR using pytesseract
        text = pytesseract.image_to_string(pil_img, config=custom_config)
        return text
    except Exception as e:
        print(f"Error in ocr_image: {e}")
        return ""

if __name__ == "__main__":
    date = str(datetime.now())
    date = date[:-10]
    date = date.replace(' ', '-')
    parser = argparse.ArgumentParser(description='Perform OCR on a scanned image.')
    parser.add_argument('image_path', 
                        type=str, 
                        nargs='?',
                        help='Path to the scanned image file') 
    args = parser.parse_args()

    # Path to the image
    image_path =  args.image_path or 'HTR/scannedImages/scanned_form.png'
    
    # Preprocess the image
    preprocessed_img = preprocess_image(image_path)

    if preprocessed_img is not None:
        # Resize the image for better OCR accuracy
        resized_img = resize_image(preprocessed_img)
        
        # Save the processed image 
        cv2.imwrite(f'HTR/processedImages/Borrow-{date}.jpg', resized_img)

        # Perform OCR on the resized image
        extracted_text = ocr_image(resized_img)

        # Print the extracted text.
        print("Extracted Text:")
        print(extracted_text)
        with open('HTR/data/data.txt', 'wt') as f:
            f.write(extracted_text)
    else:
        print("Failed to preprocess the image.")