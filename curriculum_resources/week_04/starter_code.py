"""
Week 4: Exploratory Data Analysis (EDA) & Visualization
- Load dataset and explore size/class distribution
- Automatically detect class names from subfolders
"""

import os
from PIL import Image
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# =========================
# Configuration
# =========================
DATA_ROOT = "dataset_root"  # Replace with your dataset folder

# 1. Dynamically detect class names
class_names = [
    d for d in next(os.walk(DATA_ROOT))[1]  # List subfolders only
]
class_names.sort()
print("Detected classes:", class_names)

# 2. Optional: user can overwrite class names if desired
# class_names = ["ClassA", "ClassB"]  # Uncomment to override

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
print("First 5 entries:")
print(df.head())

# =========================
# Visualize class distribution
# =========================
plt.figure(figsize=(8,5))
sns.countplot(x="class", data=df, order=class_names)
plt.title("Number of Images per Class")
plt.show()

# =========================
# Show one sample image per class
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