"""
WEEK 15 STARTER CODE
Evaluation on Unseen Data & Documentation Prep
"""

import os
import torch
from torchvision import transforms, models, datasets
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import numpy as np

# -----------------------------
# Config
# -----------------------------
DATA_ROOT = "unseen_field_data"
MODEL_PATH = "plant_classifier.pth"
BATCH_SIZE = 16

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

# -----------------------------
# Load Model
# -----------------------------
def load_model(path, num_classes):
    model = models.resnet18(pretrained=False)
    model.fc = torch.nn.Linear(model.fc.in_features, num_classes)
    model.load_state_dict(torch.load(path, map_location="cpu"))
    model.eval()
    return model

# -----------------------------
# Dataset
# -----------------------------
dataset = datasets.ImageFolder(DATA_ROOT, transform=transform)
loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=False)

class_names = dataset.classes
model = load_model(MODEL_PATH, len(class_names))

# -----------------------------
# Evaluation Function
# -----------------------------
def evaluate_model(model, loader):
    y_true = []
    y_pred = []
    with torch.no_grad():
        for imgs, labels in loader:
            outputs = model(imgs)
            _, preds = torch.max(outputs, 1)
            y_true.extend(labels.numpy())
            y_pred.extend(preds.numpy())
    return np.array(y_true), np.array(y_pred)

y_true, y_pred = evaluate_model(model, loader)

print("Classification Report:\n")
print(classification_report(y_true, y_pred, target_names=class_names))

print("\nConfusion Matrix:\n")
print(confusion_matrix(y_true, y_pred))

# -----------------------------
# Visualization Placeholder
# -----------------------------
# Students can start preparing plots for their reports
plt.figure(figsize=(8,6))
plt.imshow(confusion_matrix(y_true, y_pred), cmap='Blues')
plt.title("Confusion Matrix Heatmap")
plt.colorbar()
plt.show()