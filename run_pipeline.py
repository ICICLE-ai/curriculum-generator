import os
import re
import random
import shutil
import csv
from collections import defaultdict

from curriculum_resources.week_08.solution import (
    classify_disease,
    train_disease_classifier
)
from curriculum_resources.week_09.solution import segment_leaf
from curriculum_resources.week_10.solution import estimate_damage

# -----------------------------
# GLOBAL CONFIG
# -----------------------------
DATASET_ROOT = "/fs/ess/PAS2699/AI_Presidency_Dataset_CSG/Corn/Corn"
OUTPUT_DIR = "./AI_Pipeline_Results"
CHECKPOINT_PATH = "week8_dinov2_finetuned.pth"
MAX_IMAGES = 3
TASK_TYPE = "disease_detection"

# Canonical class names as trained — order does not matter
KNOWN_CLASSES = [
    "Corn Borer",
    "Grey Leaf Spot",
    "Healthy",
    "Herbicide Sensitivity",
    "Holcus Spot",
    "Magnesium Potassium Deficiency Amb",
    "Nitrogen Burn",
    "Nitrogen Deficiency",
    "Northern Corn Leaf Blight",
    "Phosphorus Deficiency",
    "Potassium Deficiency",
]


# -----------------------------
# HELPER: Normalize label
# -----------------------------
def normalize_label(raw_label):
    """
    Maps a raw folder name to the nearest canonical class name.

    Strategy (applied in order):
    1. Strip trailing date/numeric suffixes (e.g. _8_31_2017, _7_1_2019)
    2. Normalize whitespace and casing
    3. Find the best matching canonical class via substring or token overlap
    4. Fall back to the cleaned string if no match is found
    """
    # Step 1: strip trailing _digits patterns (dates, IDs, version numbers)
    cleaned = re.sub(r'(_\d+)+$', '', raw_label).strip()

    # Step 2: normalize casing and whitespace
    cleaned = ' '.join(cleaned.split())

    # Step 3: exact match (case-insensitive)
    for cls in KNOWN_CLASSES:
        if cleaned.lower() == cls.lower():
            return cls

    # Step 4: canonical class is substring of cleaned label (or vice versa)
    for cls in KNOWN_CLASSES:
        if cls.lower() in cleaned.lower() or cleaned.lower() in cls.lower():
            return cls

    # Step 5: token overlap — pick class with most words in common
    cleaned_tokens = set(cleaned.lower().split())
    best_match = None
    best_score = 0
    for cls in KNOWN_CLASSES:
        cls_tokens = set(cls.lower().split())
        score = len(cleaned_tokens & cls_tokens)
        if score > best_score:
            best_score = score
            best_match = cls

    if best_match and best_score > 0:
        return best_match

    # Step 6: no match found — return cleaned string as-is
    return cleaned


# -----------------------------
# HELPER: Extract Ground Truth
# -----------------------------
def extract_label_from_path(path):
    """
    Assumes folder structure:
    .../ClassName/.../image.jpg
    """
    parts = path.split(os.sep)
    raw = parts[-2] if len(parts) >= 2 else "Unknown"
    return normalize_label(raw)


# -----------------------------
# MAIN PIPELINE
# -----------------------------
def run_pipeline():
    global DATASET_ROOT, OUTPUT_DIR, MAX_IMAGES, TASK_TYPE

    if not DATASET_ROOT:
        raise ValueError("DATASET_ROOT not set")

    random.seed(42)

    print("\nStarting AI Pipeline")
    print("Task Type:", TASK_TYPE)
    print("Dataset:", DATASET_ROOT)
    print("Checkpoint:", CHECKPOINT_PATH)

    images_dir = os.path.join(OUTPUT_DIR, "images")
    segmented_dir = os.path.join(images_dir, "segmented")
    mask_dir = os.path.join(images_dir, "masks")

    os.makedirs(segmented_dir, exist_ok=True)
    os.makedirs(mask_dir, exist_ok=True)

    results_file = os.path.join(OUTPUT_DIR, "results.csv")

    if not os.path.exists(results_file):
        with open(results_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "image_path",
                "ground_truth",
                "predicted_class",
                "segmented_image",
                "mask",
                "damage_percent"
            ])

    # -----------------------------
    # TRAIN MODEL IF NEEDED
    # -----------------------------
    if TASK_TYPE == "disease_detection":
        if not os.path.exists(CHECKPOINT_PATH):
            print("\nTraining classifier...")
            train_disease_classifier(
                DATASET_ROOT,
                batch_size=4,
                save_path=CHECKPOINT_PATH,
                max_per_class=50
            )
        else:
            print("\nUsing existing trained model.")

    # -----------------------------
    # COLLECT IMAGES
    # -----------------------------
    valid_ext = (".jpg", ".jpeg", ".png", ".tif", ".tiff")
    all_images = []

    for root, _, files in os.walk(DATASET_ROOT):
        for f in files:
            if f.lower().endswith(valid_ext):
                all_images.append(os.path.join(root, f))

    if not all_images:
        raise RuntimeError("No images found in dataset")

    print("\nTotal images found:", len(all_images))

    # -----------------------------
    # SAMPLE IMAGES
    # -----------------------------
    sample_images = random.sample(all_images, min(MAX_IMAGES, len(all_images)))

    print("Processing", len(sample_images), "images...\n")

    # -----------------------------
    # METRICS TRACKING
    # -----------------------------
    correct = 0
    total = 0
    confusion = defaultdict(lambda: defaultdict(int))

    # -----------------------------
    # PROCESS IMAGES
    # -----------------------------
    for img_path in sample_images:
        print("=" * 60)
        print("Processing:", img_path)

        ground_truth = extract_label_from_path(img_path)

        predicted = "N/A"
        damage = "N/A"

        # Classification
        if TASK_TYPE == "disease_detection":
            predicted = classify_disease(img_path, model_path=CHECKPOINT_PATH)
            print("Predicted Class:", predicted)
            print("Ground Truth:", ground_truth)

            total += 1
            if predicted == ground_truth:
                correct += 1

            confusion[ground_truth][predicted] += 1

        # Segmentation
        segmented_path, mask_path = segment_leaf(
            img_path,
            output_dir=OUTPUT_DIR,
            resize=(512, 512)
        )
        print("Segmentation completed")

        final_seg = os.path.join(segmented_dir, os.path.basename(segmented_path))
        final_mask = os.path.join(mask_dir, os.path.basename(mask_path))

        shutil.move(segmented_path, final_seg)
        shutil.move(mask_path, final_mask)

        # Damage estimation
        if TASK_TYPE == "disease_detection":
            damage = estimate_damage(final_seg, final_mask)
            print("Damage %:", damage)

        with open(results_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                img_path,
                ground_truth,
                predicted,
                final_seg,
                final_mask,
                damage
            ])

    # -----------------------------
    # FINAL METRICS
    # -----------------------------
    print("\nPipeline completed successfully")
    print("Results saved in:", OUTPUT_DIR)

    if total > 0:
        accuracy = correct / total
        print("\nClassification Accuracy:", round(accuracy * 100, 2), "%")

        print("\nConfusion Matrix:")
        all_labels = sorted(set(
            list(confusion.keys()) +
            [pred for preds in confusion.values() for pred in preds]
        ))
        print("GT \\ Pred ->", all_labels)

        for gt in all_labels:
            row = [confusion[gt][pred] for pred in all_labels]
            print(gt, ":", row)

    return "Pipeline completed"


if __name__ == "__main__":
    run_pipeline()