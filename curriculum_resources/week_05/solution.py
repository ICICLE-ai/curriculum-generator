"""
Week 5 Solution: Machine Learning on Image Dataset
- Dynamic classes
- Train-test split
- KNN classification
"""

import os
from PIL import Image
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import classification_report, confusion_matrix

DATA_ROOT = "dataset_root"
IMAGE_SIZE = (64, 64)
TEST_SIZE = 0.2
RANDOM_STATE = 42

# =========================
# Detect classes dynamically
# =========================
class_names = [d for d in next(os.walk(DATA_ROOT))[1]]
class_names.sort()
print("Detected classes:", class_names)

# Optional manual override
# class_names = ["ClassA", "ClassB"]

# =========================
# Load dataset
# =========================
X, y = [], []
for idx, cls in enumerate(class_names):
    cls_path = os.path.join(DATA_ROOT, cls)
    for fname in os.listdir(cls_path):
        if fname.lower().endswith((".jpg", ".png", ".jpeg")):
            img_path = os.path.join(cls_path, fname)
            img = Image.open(img_path).convert("RGB")
            img = img.resize(IMAGE_SIZE)
            X.append(np.array(img).flatten())
            y.append(idx)

X = np.array(X)
y = np.array(y)
print("Dataset loaded. Shape:", X.shape, y.shape)

# =========================
# Train-test split
# =========================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
)

# =========================
# Train KNN
# =========================
knn = KNeighborsClassifier(n_neighbors=3)
knn.fit(X_train, y_train)

# =========================
# Evaluate
# =========================
y_pred = knn.predict(X_test)

print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=class_names))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))