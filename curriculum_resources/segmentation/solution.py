"""
WEEK 9 (UPDATED)
Leaf Segmentation using SAM (Prompt-Based - Stable)
"""

from datetime import datetime
import os
import urllib.request

import cv2
import numpy as np
from PIL import Image

import torch
from segment_anything import sam_model_registry, SamPredictor

# --------------------------------------------
# Lazy Load SAM for segmentation (if enabled)
# --------------------------------------------
SAM_VERSION = "vit_b"
predictor_cache = None

def get_sam_predictor(model_path, device):
    global predictor_cache
    # Check if model exists
    if predictor_cache is None:
        print("Loading SAM Model...")
        if not os.path.exists(model_path):
            print(f"SAM not found at {model_path}. Auto-downloading checkpoint...")
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            url = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth"
            urllib.request.urlretrieve(url, model_path)
            print("Download complete.")
    
        sam = sam_model_registry[SAM_VERSION](checkpoint=model_path)
        sam.to(device)
        sam.eval()
        predictor_cache = SamPredictor(sam)
        print("SAM loaded successfully")

    return predictor_cache

        



# ----------------------------
# Segment Object Function
# ----------------------------
def segment_object(image_path, model_path, device, output_dir=".", resize=(512,512)):

    predictor = get_sam_predictor(model_path, device)
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

    # Build the main images folder and the two subfolders
    images_dir = os.path.join(output_dir, "images")
    seg_dir = os.path.join(images_dir, "segmented")
    mask_dir = os.path.join(images_dir, "masks")
    
    # Create them on the hard drive
    os.makedirs(seg_dir, exist_ok=True)
    os.makedirs(mask_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(image_path).split(".")[0]

    # Set the paths to the subfolders
    segmented_path = os.path.join(seg_dir, f"{filename}_segmented_{timestamp}.png")
    mask_path = os.path.join(mask_dir, f"{filename}_mask_{timestamp}.png")

    # Save them
    Image.fromarray(segmented).save(segmented_path)
    Image.fromarray(mask).save(mask_path)

    return segmented_path, mask_path

# =================
# Global run batch
# =================
def run_batch(image_paths, config, stage=None, previous_results_list=None):
    # Pull from YAML

    model_path = stage.model_path if stage and stage.model_path else "sam_vit_b.pth"
    
    # Override with global cache if available
    if os.environ.get("SAM_CACHE"):
        model_path = os.path.join(os.environ.get("SAM_CACHE"), os.path.basename(model_path))
        
    output_dir = config.output.directory
    device = config.execution.device
    image_size = (config.execution.image_size, config.execution.image_size)

    # Loop through the batch
    batch_outputs = []

    for img_path in image_paths:
        segmented_path, mask_path = segment_object(
            img_path, 
            model_path=model_path, 
            device=device,
            output_dir=output_dir, 
            resize=image_size
        )
        batch_outputs.append({"segmented_image": segmented_path, "mask": mask_path})

    return batch_outputs