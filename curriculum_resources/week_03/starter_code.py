"""
Week 3: Basic Image Processing & Manipulation
- Learn to convert, filter, and modify images
- Apply simple pixel-level operations
"""

from PIL import Image, ImageEnhance, ImageFilter
import matplotlib.pyplot as plt
import numpy as np

# =============================
# Load Image
# =============================
IMAGE_PATH = "sample.jpg"  # Replace with your image path
try:
    img = Image.open(IMAGE_PATH).convert("RGB")
    plt.imshow(img)
    plt.title("Original Image")
    plt.axis("off")
    plt.show()
except FileNotFoundError:
    print("Please put an image file named 'sample.jpg' in this folder.")

# =============================
# 1. Convert to Grayscale
# =============================
gray_img = img.convert("L")
plt.imshow(gray_img, cmap="gray")
plt.title("Grayscale Image")
plt.axis("off")
plt.show()

# =============================
# 2. Adjust Brightness
# =============================
enhancer = ImageEnhance.Brightness(img)
bright_img = enhancer.enhance(1.5)  # 1.0=original, >1 brighter, <1 darker
plt.imshow(bright_img)
plt.title("Brightened Image")
plt.axis("off")
plt.show()

# =============================
# 3. Adjust Contrast
# =============================
enhancer = ImageEnhance.Contrast(img)
contrast_img = enhancer.enhance(2.0)  # Increase contrast
plt.imshow(contrast_img)
plt.title("High Contrast Image")
plt.axis("off")
plt.show()

# =============================
# 4. Blur & Edge Detection
# =============================
blur_img = img.filter(ImageFilter.GaussianBlur(3))
edge_img = img.filter(ImageFilter.FIND_EDGES)

plt.figure(figsize=(10,5))
plt.subplot(1,2,1)
plt.imshow(blur_img)
plt.title("Blurred Image")
plt.axis("off")

plt.subplot(1,2,2)
plt.imshow(edge_img)
plt.title("Edge Detection")
plt.axis("off")
plt.show()

# =============================
# 5. Pixel Manipulation (Manual)
# =============================
img_array = np.array(img)
# Increase red channel by 50 (clip to 255)
img_array[:,:,0] = np.clip(img_array[:,:,0]+50, 0, 255)

modified_img = Image.fromarray(img_array)
plt.imshow(modified_img)
plt.title("Red Boosted Image")
plt.axis("off")
plt.show()