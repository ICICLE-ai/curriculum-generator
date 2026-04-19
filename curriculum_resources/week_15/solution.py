"""
WEEK 15 SOLUTION
Evaluation & Documentation Prep
"""

import os
import torch
from torchvision import transforms, models, datasets
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

DATA_ROOT = "unseen_field_data"
MODEL_PATH = "plant_classifier.pth"
BATCH_SIZE = 16

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

# -----------------------------
# Load pre-trained model
# -----------------------------
def load_model(path, num_classes):
    model = models.resnet18(pretrained=False)
    model.fc = torch.nn.Linear(model.fc.in_features, num_classes)
    model.load_state_dict(torch.load(path, map_location="cpu"))
    model.eval()
    return model

dataset = datasets.ImageFolder(DATA_ROOT, transform=transform)
loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=False)

class_names = dataset.classes
model = load_model(MODEL_PATH, len(class_names))

# -----------------------------
# Evaluate
# -----------------------------
def evaluate_model(model, loader):
    y_true, y_pred = [], []
    with torch.no_grad():
        for imgs, labels in loader:
            outputs = model(imgs)
            probs = torch.softmax(outputs, dim=1)
            preds = torch.argmax(probs, dim=1)
            y_true.extend(labels.numpy())
            y_pred.extend(preds.numpy())
    return np.array(y_true), np.array(y_pred)

y_true, y_pred = evaluate_model(model, loader)

# -----------------------------
# Report
# -----------------------------
print("Classification Report:\n")
print(classification_report(y_true, y_pred, target_names=class_names))

print("\nConfusion Matrix:\n")
cm = confusion_matrix(y_true, y_pred)
print(cm)

# -----------------------------
# Confusion Matrix Heatmap
# -----------------------------
plt.figure(figsize=(8,6))
sns.heatmap(cm, annot=True, fmt='d', xticklabels=class_names, yticklabels=class_names, cmap="Blues")
plt.xlabel("Predicted")
plt.ylabel("True")
plt.title("Confusion Matrix Heatmap")
plt.show()

# -----------------------------
# Metrics summary for documentation
# -----------------------------
accuracy = np.sum(y_true == y_pred) / len(y_true) * 100
print(f"\nOverall Accuracy: {accuracy:.2f}%")