from PIL import Image
import matplotlib.pyplot as plt

print("Hello AI World!")

student_name = "Maya"
age = 14

print("My name is", student_name)
print("I am", age, "years old")

print("\nCounting from 1 to 5:")
for number in range(1, 6):
    print(number)

print("\nCounting from 1 to 10:")
for number in range(1, 11):
    print(number)


def greet(name):
    print("Hello", name, "! Welcome to AI class!")

greet(student_name)


def favorite_color():
    print("My favorite color is blue!")

favorite_color()


IMAGE_PATH = "sample.jpg"

img = Image.open(IMAGE_PATH)

print("\nImage size:", img.size)
print("Image mode:", img.mode)

plt.imshow(img)
plt.title("Original Image")
plt.axis("off")
plt.show()


# Rotate image
rotated = img.rotate(90)
plt.imshow(rotated)
plt.title("Rotated Image")
plt.axis("off")
plt.show()


# Grayscale image
gray = img.convert("L")
plt.imshow(gray, cmap="gray")
plt.title("Grayscale Image")
plt.axis("off")
plt.show()