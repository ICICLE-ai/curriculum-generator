"""
WEEK 9 (UPDATED)
Leaf Segmentation using SAM (Prompt-Based - Stable)
"""

from datetime import datetime
import errno
import os
import time
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


# SAM takes boxes and points, not text: Grounding DINO turns the stage's prompt into a box for SAM
TEXT_DETECTOR_ID = "IDEA-Research/grounding-dino-tiny"
BOX_THRESHOLD = 0.35
TEXT_THRESHOLD = 0.25
detector_cache = None

def get_text_detector(device):
    global detector_cache
    if detector_cache is None:
        from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor
        print(f"Loading text-prompt detector {TEXT_DETECTOR_ID}...")
        processor = AutoProcessor.from_pretrained(TEXT_DETECTOR_ID)
        model = AutoModelForZeroShotObjectDetection.from_pretrained(TEXT_DETECTOR_ID).to(device).eval()
        detector_cache = (processor, model)
    return detector_cache


def detect_prompt_box(image, prompt, device):
    """Highest-scoring box (x0, y0, x1, y1) for the text prompt in a PIL image, or None when nothing matches."""
    processor, model = get_text_detector(device)
    text = prompt.strip().lower().rstrip(".") + "."  # Grounding DINO expects lowercase phrases ending in a period
    inputs = processor(images=image, text=text, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    # Positional: the box threshold is `box_threshold` in transformers 4.49 (the container) and `threshold` later
    result = processor.post_process_grounded_object_detection(
        outputs, inputs.input_ids, BOX_THRESHOLD, TEXT_THRESHOLD, [image.size[::-1]],
    )[0]
    if len(result["scores"]) == 0:
        return None
    return result["boxes"][int(result["scores"].argmax())].tolist()





# ----------------------------
# Segment Object Function
# ----------------------------
def segment_object(image_path, model_path, device, output_dir=".", resize=(512,512), prompt=None):
    """Segments the prompt's object (the most prominent object when there is no prompt or it matches nothing).
    Returns (segmented_path, mask_path, prompt_matched)."""

    predictor = get_sam_predictor(model_path, device)
    image = Image.open(image_path).convert("RGB")

    if resize:
        image = image.resize(resize)

    image_np = np.array(image)

    predictor.set_image(image_np)

    h, w, _ = image_np.shape

    prompt_box = detect_prompt_box(image, prompt, device) if prompt and prompt.strip() else None
    input_box = np.array(prompt_box if prompt_box is not None else [0, 0, w, h])

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
    _save_png(segmented, segmented_path)
    _save_png(mask, mask_path)

    return segmented_path, mask_path, prompt_box is not None


def _save_png(array, path, attempts=3, wait_s=5):
    """Expanse's Lustre scratch intermittently fails a write with EIO (Errno 5), which ended Phase 1 in
    runs c2adab2d and 7ed996a7; a retry after a short wait rewrites the whole file."""
    for attempt in range(1, attempts + 1):
        try:
            Image.fromarray(array).save(path)
            return
        except OSError as err:
            if err.errno != errno.EIO or attempt == attempts:
                raise
            print(f"[WARN] I/O error saving {path} (attempt {attempt}/{attempts}); retrying in {wait_s}s")
            time.sleep(wait_s)

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
    prompt = (stage.prompt or "").strip() if stage else ""
    batch_outputs = []

    for img_path in image_paths:
        segmented_path, mask_path, prompt_matched = segment_object(
            img_path,
            model_path=model_path,
            device=device,
            output_dir=output_dir,
            resize=image_size,
            prompt=prompt,
        )
        batch_outputs.append({"segmented_image": segmented_path, "mask": mask_path,
                              "prompt": prompt or None, "prompt_matched": prompt_matched})

    if prompt:
        matched = sum(o["prompt_matched"] for o in batch_outputs)
        print(f"Segmentation prompt '{prompt}' matched {matched}/{len(batch_outputs)} images "
              f"(the rest outline the most prominent object)")
    return batch_outputs