"""
WEEK 9 STARTER CODE (UPDATED)
Leaf Segmentation using SAM (Prompt-Based)
"""

import torch
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

from segment_anything import sam_model_registry, SamPredictor


# --------------------------------
# Load SAM Model
# --------------------------------

CHECKPOINT = "sam_vit_b.pth"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

sam = sam_model_registry["vit_b"](checkpoint=CHECKPOINT)
sam.to(DEVICE)
sam.eval()

predictor = SamPredictor(sam)


# --------------------------------
# Load image
# --------------------------------

IMAGE_PATH = "sample_leaf.jpg"

try:
    image = np.array(Image.open(IMAGE_PATH).convert("RGB"))
except FileNotFoundError:
    print("Please place a sample leaf image named 'sample_leaf.jpg' in this folder.")
    exit()

predictor.set_image(image)

h, w, _ = image.shape


# --------------------------------
# Generate mask using bounding box
# --------------------------------

# TODO: define bounding box covering full image
input_box = None

# TODO: generate masks using predictor
masks, scores, _ = None, None, None


# --------------------------------
# Select best mask
# --------------------------------

# TODO: pick mask with highest score
best_mask = None


# --------------------------------
# Apply mask
# --------------------------------

overlay = image.copy()

# TODO: apply mask to keep only leaf
# overlay[...] = ...


# --------------------------------
# Visualize
# --------------------------------

plt.figure(figsize=(12,5))

plt.subplot(1,2,1)
plt.title("Original Image")
plt.imshow(image)
plt.axis("off")

plt.subplot(1,2,2)
plt.title("Segmented Leaf")
plt.imshow(overlay)
plt.axis("off")

plt.show()