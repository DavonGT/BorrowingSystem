import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cv2
import numpy as np
from PIL import Image
import pytesseract
import argparse
from datetime import datetime

# Ensure Tesseract is correctly set up on Windows
# For Windows, specify the location of the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe' 
# tessdata_dir = 'C:\\Program Files\\Tesseract-OCR\\tessdata' # Modify this path if needed

def get_blue(image):
    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Extract the blue channel
    blue_channel = image[:, :, 0]

    # Create a mask where the blue channel is significant
    threshold = 10  # Adjust the threshold as needed
    mask = blue_channel > threshold

    # Create an output image in grayscale
    output = cv2.merge((gray, gray, gray))

    # Replace the blue channel with the original blue values where the mask is True
    output[:, :, 0] = np.where(mask, blue_channel, gray)

    return output

def blue_only(image):
    # Load the image
    image = cv2.imread(image_path)

    # Convert the image to the HSV color space
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define the range for the color blue in HSV
    lower_blue = np.array([90, 90, 90])  # Lower bound for blue
    upper_blue = np.array([130, 255, 255])  # Upper bound for blue

    # Create a mask for blue colors
    blue_mask = cv2.inRange(hsv_image, lower_blue, upper_blue)

    # Create a white background
    white_background = np.ones_like(image) * 255

    # Combine the mask with the original image to keep only blue areas
    blue_only = cv2.bitwise_and(image, image, mask=blue_mask)

    # Replace non-blue areas with white
    result = white_background.copy()
    result[blue_mask > 0] = blue_only[blue_mask > 0]

    return result

def preprocess_image(image_path):
    """Load and preprocess the image for better OCR accuracy."""
    try:
        # Read the image using OpenCV
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Image at {image_path} could not be loaded.")

        img = get_blue(img)
        img = blue_only(img)
        return img
        
    except Exception as e:
        print(f"Error preprocessing image: {str(e)}")
        return None

def resize_image(image):
    """Resize the image to a smaller size for faster processing."""
    
    image = get_blue(image)
    image = blue_only(image)

    h, w = image.shape[:2]
    image = image[int(h * .375): h - int(h * .2)  , :w ]

    return image

def ocr_image(image):
    """Perform OCR on the preprocessed image."""
    try:
        # Custom configuration for tesseract (LSTM OCR engine, automatic page segmentation)
        custom_config = ' --psm 6 --oem 3'

        # Perform OCR using pytesseract
        text = pytesseract.image_to_string(image, config=custom_config, lang='eng+spa+fil')
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
    image_path = args.image_path or 'HTR\\scannedImages\\scanned_form.png'  # Use Windows-style path
    
    # Preprocess the image
    preprocessed_img = preprocess_image(image_path)
    preprocessed_img = blue_only(preprocessed_img)

    if preprocessed_img is not None:
        data_dir = 'HTR\\data'
        processed_images_dir = 'HTR\\processedImages'
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        if not os.path.exists(processed_images_dir):
            os.makedirs(processed_images_dir)

        # Process the image
        resized_img = resize_image(preprocessed_img)

        # Verify the image processing
        if resized_img is None:
            print("Failed to process the image.")
        else:
            print("Image processed successfully.")

        # Save the processed image
        processed_image_path = os.path.join(processed_images_dir, f'Borrowme.jpg')  # Windows-style path
        cv2.imwrite(processed_image_path, resized_img)

        # Perform OCR on the resized image
        extracted_text = ocr_image(processed_image_path)

        # Print the extracted text
        print("Extracted Text:")
        print(extracted_text)

        # Save the extracted text to a file
        try:
            with open(os.path.join(data_dir, 'data.txt'), 'wt') as f:  # Windows-style path for saving text
                f.write(extracted_text)
            print("Extracted text saved successfully.")
        except Exception as e:
            print(f"Failed to save extracted text: {e}")