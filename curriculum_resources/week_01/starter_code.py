"""
WEEK 1 STARTER CODE
Python + Images Exploration
"""

# Basic printing
print("Hello AI World!")

# Variables
student_name = "Your Name Here"
age = 12  # TODO: Change this to your real age

print("My name is", student_name)
print("I am", age, "years old")

# Simple loop
print("\nCounting from 1 to 5:")
for number in range(1, 6):
    print(number)

# TODO:
# Make another loop that counts from 1 to 10


#  Simple function
def greet(name):
    print("Hello", name, "! Welcome to AI class!")

greet(student_name)

# TODO:
# Create a new function called favorite_color()
# It should print your favorite color.


#  Working with images
from PIL import Image
import matplotlib.pyplot as plt

IMAGE_PATH = "sample.jpg"  # TODO: Replace with your image

try:
    img = Image.open(IMAGE_PATH)

    print("\nImage size:", img.size)
    print("Image mode:", img.mode)

    plt.imshow(img)
    plt.title("My Image")
    plt.axis("off")
    plt.show()

except FileNotFoundError:
    print("\nPlease put an image file named 'sample.jpg' in this folder.")

# TODO:
# Try rotating the image.
# Try converting it to grayscale.