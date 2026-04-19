"""
WEEK 16 SOLUTION
Final Evaluation & Presentation Prep
"""

import os
import torch
from torchvision import transforms, datasets, models
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# -----------------------------
# Configuration
# -----------------------------
DATA_ROOT = "final_field_test_data"
MODEL_PATH = "plant_classifier.pth"
OUTPUT_DIR = "week16_final_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
BATCH_SIZE = 16

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

# -----------------------------
# Load model
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
# Evaluate on final unseen data
# -----------------------------
y_true, y_pred = [], []

with torch.no_grad():
    for imgs, labels in loader:
        outputs = model(imgs)
        probs = torch.softmax(outputs, dim=1)
        preds = torch.argmax(probs, dim=1)
        y_true.extend(labels.numpy())
        y_pred.extend(preds.numpy())

# -----------------------------
# Save classification report
# -----------------------------
report = classification_report(y_true, y_pred, target_names=class_names)
with open(os.path.join(OUTPUT_DIR, "classification_report.txt"), "w") as f:
    f.write(report)

# -----------------------------
# Confusion Matrix Visualization
# -----------------------------
cm = confusion_matrix(y_true, y_pred)
plt.figure(figsize=(8,6))
sns.heatmap(cm, annot=True, fmt='d', xticklabels=class_names, yticklabels=class_names, cmap="Blues")
plt.xlabel("Predicted")
plt.ylabel("True")
plt.title("Final Confusion Matrix")
plt.savefig(os.path.join(OUTPUT_DIR, "confusion_matrix.png"))
plt.close()

# -----------------------------
# Metrics Summary
# -----------------------------
accuracy = np.sum(np.array(y_true) == np.array(y_pred)) / len(y_true) * 100
print(f"Overall Accuracy on final unseen dataset: {accuracy:.2f}%")
print("✅ Final outputs, plots, and reports saved. Ready for presentation and video creation.")