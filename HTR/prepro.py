import cv2
import numpy as np

# Load the image
image = cv2.imread('../media/captured_image.png')

# Convert the image to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Extract the blue channel
blue_channel = image[:, :, 0]

# Create a mask where the blue channel is significant
threshold = 0  # Adjust the threshold as needed
mask = blue_channel > threshold

# Create an output image in grayscale
output = cv2.merge((gray, gray, gray))

# Replace the blue channel with the original blue values where the mask is True
output[:, :, 0] = np.where(mask, blue_channel, gray)

# Save the blue channel as a new image
cv2.imwrite('blueonly.jpg', output)

#Load the image
image = cv2.imread('blueonly.jpg')

# Convert the image to the HSV color space
hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Define the range for the color blue in HSV
lower_blue = np.array([90, 35, 25])   # Lower bound for blue
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

# Save and display the result
cv2.imwrite('output.jpg', result)
