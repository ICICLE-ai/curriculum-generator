"""
WEEK 9 (UPDATED)
Leaf Segmentation using SAM (Prompt-Based - Stable)
"""

import torch
import numpy as np
import cv2
import os
from PIL import Image
from datetime import datetime
from segment_anything import sam_model_registry, SamPredictor

# ----------------------------
# Config
# ----------------------------
SAM_VERSION = "vit_b"
CHECKPOINT = "/fs/ess/PAS2699/mhole/curriculum_generator/Code/sam_vit_b.pth"
IMAGE_SIZE = (512, 512)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ----------------------------
# Load SAM once
# ----------------------------
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


# ----------------------------
# Segment Leaf Function
# ----------------------------
def segment_leaf(image_path, output_dir=".", resize=IMAGE_SIZE):

    image = Image.open(image_path).convert("RGB")

    if resize:
        image = image.resize(resize)

    image_np = np.array(image)

    predictor.set_image(image_np)

    h, w, _ = image_np.shape

    input_box = np.array([0, 0, w, h])

    masks, scores, _ = predictor.predict(
        box=input_box,
        multimask_output=True
    )

    if masks is None or len(masks) == 0:
        raise RuntimeError("No masks generated")

    best_mask = masks[np.argmax(scores)]

    mask = best_mask.astype(np.uint8) * 255

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    segmented = image_np.copy()
    segmented[mask == 0] = 0

    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(image_path).split(".")[0]

    segmented_path = os.path.join(output_dir, f"{filename}_segmented_{timestamp}.png")
    mask_path = os.path.join(output_dir, f"{filename}_mask_{timestamp}.png")

    Image.fromarray(segmented).save(segmented_path)
    Image.fromarray(mask).save(mask_path)

    return segmented_path, mask_path