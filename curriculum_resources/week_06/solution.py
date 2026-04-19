"""
Week 6 Solution: Complete Preprocessing & Augmentation Pipeline
"""

import os
import numpy as np
from PIL import Image, ImageEnhance
import random

DATA_ROOT = "dataset_root"
IMAGE_SIZE = (128, 128)
NORMALIZE = True
AUGMENT = True


def preprocess_image(img_path):
    try:
        img = Image.open(img_path).convert("RGB")
        img = img.resize(IMAGE_SIZE)

        img_array = np.array(img)

        if NORMALIZE:
            img_array = img_array / 255.0

        return img_array

    except Exception:
        print(f"Skipping corrupted image: {img_path}")
        return None


def augment_image(img_array):
    img = Image.fromarray((img_array * 255).astype(np.uint8))

    # Random rotation
    if random.random() > 0.5:
        angle = random.randint(-20, 20)
        img = img.rotate(angle)

    # Random horizontal flip
    if random.random() > 0.5:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)

    # Random brightness adjustment
    if random.random() > 0.5:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(random.uniform(0.7, 1.3))

    img_array = np.array(img)

    if NORMALIZE:
        img_array = img_array / 255.0

    return img_array


# Example processing
processed_images = []

for root, dirs, files in os.walk(DATA_ROOT):
    for fname in files:
        if fname.lower().endswith((".jpg", ".png", ".jpeg")):
            img_path = os.path.join(root, fname)

            img = preprocess_image(img_path)

            if img is not None:
                if AUGMENT:
                    img = augment_image(img)

                processed_images.append(img)

processed_images = np.array(processed_images)

print("Final processed dataset shape:", processed_images.shape)