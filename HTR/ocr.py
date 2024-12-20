import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cv2
import numpy as np
from PIL import Image
import pytesseract
import argparse
from datetime import datetime
import math
from scipy import ndimage

from HTR.aruco_crop import crop_using_aruco as crop

# pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract'

def calculate_skew_angle(image):
    """Calculate the skew angle of the image."""
    # Convert to grayscale and threshold
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    
    # Find all non-zero points
    coords = np.column_stack(np.where(thresh > 0))
    
    # Find the angle
    angle = cv2.minAreaRect(coords)[-1]
    
    if angle < -45:
        angle = 90 + angle
    
    return -1.0 * angle

def deskew_image(image):
    """Deskew the image using calculated angle."""
    angle = calculate_skew_angle(image)
    if abs(angle) > 0.5:  # Only deskew if angle is significant
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated
    return image

def remove_noise(image):
    """Remove noise from the image."""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply bilateral filter to remove noise while preserving edges
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)
    
    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # Morphological operations to remove small noise
    kernel = np.ones((2,2), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    return cleaned

def enhance_contrast(image):
    """Enhance contrast using CLAHE."""
    # Convert to LAB color space
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    cl = clahe.apply(l)
    
    # Merge channels
    enhanced_lab = cv2.merge((cl,a,b))
    
    # Convert back to BGR
    enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    return enhanced_bgr

def detect_blue_ink(image):
    """Improved blue ink detection with dynamic thresholding."""
    # Convert to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Calculate average saturation and value
    avg_s = np.mean(hsv[:,:,1])
    avg_v = np.mean(hsv[:,:,2])
    
    # Dynamic thresholds based on image characteristics
    lower_blue = np.array([90, max(25, avg_s/2), max(25, avg_v/2)])
    upper_blue = np.array([130, 255, 255])
    
    # Create mask
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    
    # Apply morphological operations to improve mask
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    return mask

def preprocess_image(image_path, crop_path):
    """Load and preprocess the image for better OCR accuracy."""
    try:
        # Read the image using OpenCV
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Image at {image_path} could not be loaded.")

        # Crop using ArUco markers
        cropped = crop(image_path, crop_path)
        
        # Enhance contrast
        enhanced = enhance_contrast(cropped)
        
        # Deskew the image
        deskewed = deskew_image(enhanced)
        
        # Detect blue ink with improved method
        blue_mask = detect_blue_ink(deskewed)
        
        # Remove noise and apply adaptive thresholding
        cleaned = remove_noise(deskewed)
        
        # Combine blue ink mask with cleaned image
        result = cv2.bitwise_and(cleaned, cleaned, mask=blue_mask)
        
        # Save intermediate results for debugging
        debug_path = os.path.join(os.path.dirname(crop_path), 'debug')
        os.makedirs(debug_path, exist_ok=True)
        
        cv2.imwrite(os.path.join(debug_path, 'enhanced.png'), enhanced)
        cv2.imwrite(os.path.join(debug_path, 'deskewed.png'), deskewed)
        cv2.imwrite(os.path.join(debug_path, 'blue_mask.png'), blue_mask)
        cv2.imwrite(os.path.join(debug_path, 'cleaned.png'), cleaned)
        cv2.imwrite(os.path.join(debug_path, 'final.png'), result)
        
        return result
        
    except Exception as e:
        print(f"Error preprocessing image: {str(e)}")
        return None

def resize_image(image, scale_factor=2):
    """Resize the image to improve OCR accuracy."""
    try:
        height, width = image.shape
        new_size = (width * scale_factor, height * scale_factor)
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
    crop_path = f'HTR/croppedImages/Borrow-{date}.jpg'

    # Preprocess the image
    preprocessed_img = preprocess_image(image_path, crop_path)

    if preprocessed_img is not None:
        # Resize the image for better OCR accuracy
        resized_img = resize_image(preprocessed_img)
        
        # Save the processed image 
        cv2.imwrite(f'HTR/processedImages/Borrow-{date}.jpg', resized_img)
        # Save on Training folder
        cv2.imwrite(f'HTR/trainingImages/Borrow-{date}.jpg', resized_img)

        # Perform OCR on the resized image
        extracted_text = ocr_image(resized_img)

        # Print the extracted text.
        print(date)
        print("Extracted Text:")
        print(extracted_text)
        with open('HTR/data/data.txt','wt') as f:
            f.write(extracted_text)
    else:
        print("Failed to preprocess the image.")
