"""
Week 8 - Transfer Learning with DINOv2
Classify corn diseases using a pre-trained vision model.
SOLUTION CODE — instructor reference only, do not share with students.
"""

import os
import shutil
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report
import numpy as np
import timm
from PIL import Image

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ======================
# Helper: build train/test folders
# ======================
def create_train_test_split(dataset_root, train_ratio=0.8, max_per_class=None):
    train_path  = os.path.join(dataset_root, "train")
    test_path   = os.path.join(dataset_root, "test")
    ignore_list = ["train", "test", "AI_Pipeline_Results", "curriculum_resources", "NeuralNetDevelopment"]

    os.makedirs(train_path, exist_ok=True)
    os.makedirs(test_path,  exist_ok=True)

    classes = [
        d for d in os.listdir(dataset_root)
        if os.path.isdir(os.path.join(dataset_root, d))
        and not d.startswith(".")
        and d not in ignore_list
    ]

    for cls in classes:
        imgs = []
        for dirpath, _, files in os.walk(os.path.join(dataset_root, cls)):
            if any(p in ["train", "test"] or p.startswith(".") for p in dirpath.split(os.sep)):
                continue
            for f in files:
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff")):
                    imgs.append(os.path.join(dirpath, f))

        if not imgs:
            print(f"Warning: No images found for class '{cls}', skipping.")
            continue

        if max_per_class is not None:
            imgs = imgs[:max_per_class]

        n_train = int(len(imgs) * train_ratio)

        for dest_folder, subset in [
            (os.path.join(train_path, cls), imgs[:n_train]),
            (os.path.join(test_path,  cls), imgs[n_train:]),
        ]:
            os.makedirs(dest_folder, exist_ok=True)
            for f in subset:
                shutil.copy(f, os.path.join(dest_folder, os.path.basename(f)))

    print("Train/test split ready:", train_path, test_path)
    return train_path, test_path


# ======================
# Train classifier
# ======================
def train_disease_classifier(
    dataset_root,
    batch_size=32,
    epochs_head=5,
    epochs_fine=3,
    save_path="week8_dinov2_finetuned.pth",
    max_per_class=None,
):
    for folder in ["train", "test"]:
        p = os.path.join(dataset_root, folder)
        if os.path.exists(p):
            shutil.rmtree(p)

    train_path, test_path = create_train_test_split(
        dataset_root, max_per_class=max_per_class
    )

    # TODO 1 SOLUTION — transforms
    train_transform = transforms.Compose([
        transforms.Resize((518, 518)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ToTensor(),
    ])

    test_transform = transforms.Compose([
        transforms.Resize((518, 518)),
        transforms.ToTensor(),
    ])

    train_dataset = datasets.ImageFolder(root=train_path, transform=train_transform)
    test_dataset  = datasets.ImageFolder(root=test_path,  transform=test_transform)

    non_empty = [
        d for d in os.listdir(train_path)
        if os.path.isdir(os.path.join(train_path, d))
        and os.listdir(os.path.join(train_path, d))
    ]
    if not non_empty:
        raise RuntimeError(f"No valid images found in {train_path}.")

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader  = DataLoader(test_dataset,  batch_size=batch_size, shuffle=False)

    class_names = train_dataset.classes
    num_classes = len(class_names)
    print(f"Found {len(train_dataset)} images across {num_classes} classes.")
    print("Classes:", class_names)

    # TODO 2 SOLUTION — load DINOv2, freeze backbone, replace head
    model = timm.create_model("vit_base_patch14_dinov2.lvd142m", pretrained=True)

    for param in model.parameters():
        param.requires_grad = False

    in_features = model.num_features
    model.head  = nn.Linear(in_features, num_classes)
    model       = model.to(DEVICE)

    criterion = nn.CrossEntropyLoss()

    # TODO 3 SOLUTION — head training loop
    print("\nTraining classifier head...\n")
    optimizer = optim.Adam(model.head.parameters(), lr=0.001)

    for epoch in range(epochs_head):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            optimizer.zero_grad()
            outputs = model(images)
            loss    = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        print(f"Epoch {epoch+1}/{epochs_head}, Loss: {running_loss:.4f}")

    # TODO 4 SOLUTION — fine-tuning loop
    print("\nFine-tuning last transformer block...\n")
    for param in model.blocks[-1].parameters():
        param.requires_grad = True
    optimizer = optim.Adam(model.parameters(), lr=1e-5)

    for epoch in range(epochs_fine):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            optimizer.zero_grad()
            outputs = model(images)
            loss    = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        print(f"Fine Epoch {epoch+1}/{epochs_fine}, Loss: {running_loss:.4f}")

    print("Fine-tuning complete!")

    # ======================
    # Evaluation
    # ======================
    model.eval()
    all_preds, all_labels = [], []
    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            outputs = model(images)
            preds   = torch.argmax(outputs, dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    accuracy = np.mean(np.array(all_preds) == np.array(all_labels))
    print(f"\nTest Accuracy: {accuracy:.4f}")
    print(classification_report(all_labels, all_preds, target_names=class_names))

    torch.save({"model_state": model.state_dict(), "class_names": class_names}, save_path)
    print("Model saved successfully at", save_path)


# ======================
# Inference
# ======================
def classify_disease(image_path, model_path="week8_dinov2_finetuned.pth"):
    checkpoint  = torch.load(model_path, map_location=DEVICE)
    class_names = checkpoint["class_names"]
    num_classes = len(class_names)

    model = timm.create_model("vit_base_patch14_dinov2.lvd142m", pretrained=False)
    in_features = model.num_features
    model.head  = nn.Linear(in_features, num_classes)
    model.load_state_dict(checkpoint["model_state"])
    model       = model.to(DEVICE).eval()

    transform = transforms.Compose([
        transforms.Resize((518, 518)),
        transforms.ToTensor(),
    ])

    img = Image.open(image_path).convert("RGB")
    img = transform(img).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        output = model(img)
        pred   = torch.argmax(output, dim=1).item()

    return class_names[pred]


# ======================
# Standalone run
# ======================
if __name__ == "__main__":
    DATASET_ROOT = "/fs/ess/PAS2699/AI_Presidency_Dataset_CSG/Soybeans/Soybeans"
    train_disease_classifier(DATASET_ROOT, max_per_class=2)