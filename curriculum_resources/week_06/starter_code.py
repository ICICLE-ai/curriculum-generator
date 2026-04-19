"""
Week 6: Data Preprocessing & Augmentation
- Resize images
- Normalize pixel values
- Basic augmentation techniques
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
    """
    Steps:
    1. Open image safely
    2. Convert to RGB
    3. Resize
    4. Normalize (optional)
    """
    try:
        img = Image.open(img_path).convert("RGB")

        # TODO: Resize image
        # TODO: Convert to numpy array
        # TODO: Normalize if NORMALIZE = True

        return img

    except Exception as e:
        print(f"Skipping corrupted image: {img_path}")
        return None


def augment_image(img):
    """
    Apply simple augmentations:
    - Random rotation
    - Random brightness change
    - Random horizontal flip
    """
    # TODO: Add augmentation logic
    return img


# Example usage
for root, dirs, files in os.walk(DATA_ROOT):
    for fname in files:
        if fname.lower().endswith((".jpg", ".png", ".jpeg")):
            img_path = os.path.join(root, fname)

            img = preprocess_image(img_path)

            if img and AUGMENT:
                img = augment_image(img)