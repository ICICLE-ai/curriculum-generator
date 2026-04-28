"""
WEEK 9 STARTER CODE (UPDATED)
Leaf Segmentation using SAM (Prompt-Based)
"""

import torch
import numpy as np
import cv2
import os
from PIL import Image
import matplotlib.pyplot as plt
from datetime import datetime

from segment_anything import sam_model_registry, SamPredictor


# --------------------------------
# Config
# --------------------------------

SAM_VERSION = "vit_b"
CHECKPOINT = "/fs/ess/PAS2699/mhole/curriculum_generator/Code/sam_vit_b.pth"
IMAGE_SIZE = (512, 512)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# --------------------------------
# Load SAM Model
# --------------------------------

print("Loading SAM model...")

if not os.path.exists(CHECKPOINT):
    raise FileNotFoundError(
        f"\n[SAM] Checkpoint not found at: {CHECKPOINT}\n"
        f"Make sure sam_vit_b.pth is located at:\n"
        f"  /fs/ess/PAS2699/mhole/curriculum_generator/Code/sam_vit_b.pth\n"
        f"Download it from: https://github.com/facebookresearch/segment-anything#model-checkpoints"
    )

sam = sam_model_registry[SAM_VERSION](checkpoint=CHECKPOINT)
sam.to(DEVICE)
sam.eval()

predictor = SamPredictor(sam)

print("SAM loaded successfully")


# --------------------------------
# Load and resize image
# --------------------------------

IMAGE_PATH = "sample_leaf.jpg"

try:
    image = Image.open(IMAGE_PATH).convert("RGB")
except FileNotFoundError:
    print("Please place a sample leaf image named 'sample_leaf.jpg' in this folder.")
    exit()

# TODO: resize image to IMAGE_SIZE
image = None

image_np = np.array(image)

predictor.set_image(image_np)

h, w, _ = image_np.shape


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
# Post-process mask
# --------------------------------

# TODO: convert best_mask to uint8 (0 or 255)
mask = None

# TODO: apply morphological closing with a 5x5 kernel
kernel = np.ones((5, 5), np.uint8)
mask = None


# --------------------------------
# Apply mask
# --------------------------------

segmented = image_np.copy()

# TODO: apply mask to keep only leaf (set background to 0)
# segmented[...] = ...


# --------------------------------
# Save outputs
# --------------------------------

OUTPUT_DIR = "."
os.makedirs(OUTPUT_DIR, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = os.path.basename(IMAGE_PATH).split(".")[0]

# TODO: save segmented image and mask to OUTPUT_DIR using timestamp and filename
segmented_path = os.path.join(OUTPUT_DIR, f"{filename}_segmented_{timestamp}.png")
mask_path = os.path.join(OUTPUT_DIR, f"{filename}_mask_{timestamp}.png")

# Image.fromarray(...).save(segmented_path)
# Image.fromarray(...).save(mask_path)


# --------------------------------
# Visualize
# --------------------------------

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.title("Original Image")
plt.imshow(image_np)
plt.axis("off")

plt.subplot(1, 2, 2)
plt.title("Segmented Leaf")
plt.imshow(segmented)
plt.axis("off")

plt.show()