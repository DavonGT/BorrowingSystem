import cv2
import numpy as np
from datetime import datetime

# Get current date and time for file naming
date = str(datetime.now())
date = date[:-6]  # Remove last 6 characters for simpler date format (like '2024-12-21 14:05')

# Sort corners function to organize corner points in correct order
def sort_corners(corners):
    # Sort based on the sum of coordinates (x + y)
    corners = sorted(corners, key=lambda x: (x[0] + x[1]))

    # Sort the remaining two by difference (x - y)
    top_left, bottom_right = corners[0], corners[3]
    remaining = sorted(corners[1:3], key=lambda x: x[0] - x[1])
    top_right, bottom_left = remaining[1], remaining[0]

    return np.array([top_left, top_right, bottom_right, bottom_left], dtype="float32")

# Crop image using ArUco markers
def crop_using_aruco(image_path, output_path='HTR\\croppedImages\\crop{}.png'.format(date)):
    # Load the scanned image
    img = cv2.imread(image_path)

    # Create a dictionary of ArUco markers
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    detector = cv2.aruco.ArucoDetector(aruco_dict)
    
    # Detect ArUco markers in the image
    corners, ids, _ = detector.detectMarkers(img)

    print("Detected corners:", corners)
    print("Detected IDs:", ids)

    if ids is not None and len(ids) == 4:
        # Sort the corners based on their IDs
        sorted_indices = np.argsort(ids.flatten())
        sorted_corners = [corners[i][0][0] for i in sorted_indices]

        # Sort corners in the correct order
        src_pts = sort_corners(sorted_corners)

        # Print sorted corners for debugging
        print("Sorted corners (src_pts):", src_pts)

        # Define the destination points for cropping
        width = int(np.linalg.norm(src_pts[1] - src_pts[0]))  # Width based on distance between top-left and top-right
        height = int(np.linalg.norm(src_pts[2] - src_pts[1]))  # Height based on distance between top-right and bottom-right
        
        dst_pts = np.array([[0, 0],  # Top-left
                            [width - 1, 0],  # Top-right
                            [width - 1, height - 1],  # Bottom-right
                            [0, height - 1]], dtype="float32")  # Bottom-left

        # Compute the perspective transform matrix
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)

        # Apply the perspective transformation to get the cropped form
        cropped = cv2.warpPerspective(img, M, (width, height))

        # Save the cropped image
        cv2.imwrite(output_path, cropped)

        print(f"Image successfully cropped and saved to {output_path}")
        return cropped

    else:
        print(f"Error: Detected {len(ids) if ids is not None else 0} markers. Exactly 4 markers are required.")

# Main function to run the cropping
if __name__ == '__main__':
    # Example usage
    crop_using_aruco(r'HTR\forms-0.jpg')  # Windows file path, raw string for compatibility
