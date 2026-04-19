import os
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


# -----------------------------
# HELPER: Extract Ground Truth
# -----------------------------
def extract_label_from_path(path):
    """
    Assumes folder structure:
    .../ClassName/.../image.jpg
    """
    parts = path.split(os.sep)
    return parts[-2] if len(parts) >= 2 else "Unknown"


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

            # Accuracy tracking
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

        # Save results
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
        classes = sorted(confusion.keys())
        print("GT \\ Pred ->", classes)

        for gt in classes:
            row = [confusion[gt][pred] for pred in classes]
            print(gt, ":", row)

    return "Pipeline completed"


if __name__ == "__main__":
    run_pipeline()