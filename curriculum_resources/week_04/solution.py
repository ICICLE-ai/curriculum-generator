"""
Week 4 Solution: EDA & Visualization (Generalizable)
- Dynamically detect classes
- Dataset inspection, class counts, and sample images
"""

import os
from PIL import Image
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

DATA_ROOT = "dataset_root"

# =========================
# Detect classes dynamically
# =========================
class_names = [d for d in next(os.walk(DATA_ROOT))[1]]
class_names.sort()
print("Detected classes:", class_names)

# Optional override
# class_names = ["ClassA", "ClassB"]  # Uncomment to overwrite

# =========================
# Build dataset info
# =========================
dataset_info = []
for cls in class_names:
    cls_path = os.path.join(DATA_ROOT, cls)
    for fname in os.listdir(cls_path):
        if fname.lower().endswith((".jpg", ".png", ".jpeg")):
            dataset_info.append({"filename": fname, "class": cls})

df = pd.DataFrame(dataset_info)

# =========================
# Inspect dataset
# =========================
print("First 5 entries:")
print(df.head())
print("\nClass distribution:")
print(df["class"].value_counts())

# =========================
# Sample images per class
# =========================
plt.figure(figsize=(12,6))
for i, cls in enumerate(class_names):
    cls_path = os.path.join(DATA_ROOT, cls)
    img_path = os.path.join(cls_path, os.listdir(cls_path)[0])
    img = Image.open(img_path).convert("RGB")
    plt.subplot(1, len(class_names), i+1)
    plt.imshow(img)
    plt.title(cls)
    plt.axis("off")
plt.show()