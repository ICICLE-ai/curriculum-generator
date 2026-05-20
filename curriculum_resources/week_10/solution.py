"""
WEEK 10 (UPDATED)
Damage Percentage Estimation (HSV-Based + Mask-Aware)
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt


def estimate_damage(image_path, mask_path, visualize=False):

    image = cv2.imread(image_path)
    mask = cv2.imread(mask_path, 0)  # grayscale mask

    if image is None or mask is None:
        raise FileNotFoundError("Image or mask not found")

    # ----------------------------
    # Convert to HSV
    # ----------------------------
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Detect damaged regions (brown/yellow)
    lower = np.array([10, 50, 50])
    upper = np.array([35, 255, 255])

    damage_mask = cv2.inRange(hsv, lower, upper)

    # Apply leaf mask
    damage_mask = cv2.bitwise_and(damage_mask, damage_mask, mask=mask)

    # ----------------------------
    # Pixel counting
    # ----------------------------
    damaged_pixels = np.sum(damage_mask == 255)
    leaf_pixels = np.sum(mask == 255)

    if leaf_pixels == 0:
        damage_percentage = 0
    else:
        damage_percentage = (damaged_pixels / leaf_pixels) * 100

    # ----------------------------
    # Visualization
    # ----------------------------
    if visualize:

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
        plt.title(f"Damage: {damage_percentage:.2f}%")
        plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        plt.axis("off")

        plt.show()

    return round(damage_percentage, 2)

# =================
# Global run stage
# =================
def run_stage(image_path, config, stage=None, previous_results=None):
    if not previous_results or "mask" not in previous_results:
        raise ValueError("Damage estimation requires a mask from the segmentation stage")
    
    mask_path = previous_results["mask"]
    calculated_value = estimate_damage(image_path, mask_path)

    # Dynamically pull the metric from the YAML
    metric_name = getattr(stage, "target_metric", "metric_result")

    return {"metric_name": calculated_value}