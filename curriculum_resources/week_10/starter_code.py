"""
WEEK 10 STARTER CODE (UPDATED)
Damage Percentage Estimation (HSV-Based)
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt


# TODO: Replace with segmented leaf image and mask from Week 9
IMAGE_PATH = "segmented_leaf.png"
MASK_PATH = "leaf_mask.png"


# Load image
image = cv2.imread(IMAGE_PATH)
mask = cv2.imread(MASK_PATH, 0)

if image is None or mask is None:
    print("Segmented image or mask not found.")
    exit()


# --------------------------------
# Convert to HSV
# --------------------------------

# TODO: convert image to HSV
hsv = None


# --------------------------------
# Detect damaged regions
# --------------------------------

# Hint: brown/yellow areas = damage

# TODO: define HSV range
lower = None
upper = None

# TODO: create damage mask
damage_mask = None


# --------------------------------
# Apply leaf mask
# --------------------------------

# TODO: apply mask so only leaf area is considered
# damage_mask = ...


# --------------------------------
# Count pixels
# --------------------------------

# TODO: count damaged pixels
damaged_pixels = None

# TODO: count total leaf pixels
leaf_pixels = None


# --------------------------------
# Calculate damage percentage
# --------------------------------

# TODO: compute damage percentage
damage_percentage = None


print("Damage percentage:", damage_percentage)


# --------------------------------
# Visualization
# --------------------------------

plt.figure(figsize=(12,5))

plt.subplot(1,3,1)
plt.title("Leaf Mask")
plt.imshow(mask, cmap="gray")
plt.axis("off")

plt.subplot(1,3,2)
plt.title("Damage Mask")
plt.imshow(damage_mask, cmap="gray")
plt.axis("off")

plt.subplot(1,3,3)
plt.title("Segmented Leaf")
plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
plt.axis("off")

plt.show()