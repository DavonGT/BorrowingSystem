#Install dependencies in your project directory
# pip install moondream

import moondream as md
from PIL import Image

# Initialize with API key
model = md.vl(api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlfaWQiOiI4Mjc2NGQ3MS1lZjE5LTQyMWQtOWVlYi1lM2RmMDE3OGJlZWYiLCJpYXQiOjE3MzUyMDU2NzB9.naoMAjwOxU4IhQqQXWe3LmOiZZ1JSYwdyMoh6af70Zg")

# Load an image
image = Image.open("./output.jpg")
encoded_image = model.encode_image(image)  # Encode image (recommended for multiple operations)


# Ask a question
answer = model.query(encoded_image, 
"""
Extract all of texts from the image.
Answer just like how the text is on the image.
Separate each text with a space.
""")["answer"]
print("Answer:", answer)
lines = answer.split(",")
file_name = "HTR/data/data.txt"
with open(file_name, "w") as f:
    for line in lines:
        f.write(line + "\n")

# Read all lines except the first
with open(file_name, "r") as file:
    lines = file.readlines()

# Write the remaining lines back to the file
with open(file_name, "w") as file:
    file.writelines(lines[1:])
