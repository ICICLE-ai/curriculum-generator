"""
Week 3 Solution Code
- Fully working solutions for grayscale, brightness, contrast, blur, edges, pixel modification
"""

from PIL import Image, ImageEnhance, ImageFilter
import matplotlib.pyplot as plt
import numpy as np

IMAGE_PATH = "sample.jpg"

try:
    img = Image.open(IMAGE_PATH).convert("RGB")

    # 1. Grayscale
    gray_img = img.convert("L")

    # 2. Brightness
    bright_img = ImageEnhance.Brightness(img).enhance(1.5)

    # 3. Contrast
    contrast_img = ImageEnhance.Contrast(img).enhance(2.0)

    # 4. Blur and Edges
    blur_img = img.filter(ImageFilter.GaussianBlur(3))
    edge_img = img.filter(ImageFilter.FIND_EDGES)

    # 5. Pixel-level manipulation (red boost)
    img_array = np.array(img)
    img_array[:,:,0] = np.clip(img_array[:,:,0]+50, 0, 255)
    red_boost_img = Image.fromarray(img_array)

    # Visualization
    plt.figure(figsize=(12,8))
    images = [img, gray_img, bright_img, contrast_img, blur_img, edge_img, red_boost_img]
    titles = ["Original", "Grayscale", "Brightened", "High Contrast", "Blurred", "Edge Detection", "Red Boosted"]
    for i, (im, t) in enumerate(zip(images, titles), 1):
        plt.subplot(2,4,i)
        plt.imshow(im if i!=2 else im, cmap="gray" if i==2 else None)
        plt.title(t)
        plt.axis("off")
    plt.tight_layout()
    plt.show()

except FileNotFoundError:
    print("Please put an image file named 'sample.jpg' in this folder.")