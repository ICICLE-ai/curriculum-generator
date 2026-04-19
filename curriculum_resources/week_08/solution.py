"""
Week 8 - DINO2 Transfer Learning + Fine-Tuning + Evaluation
Dynamic recursive dataset handling, safe train/test split, ignoring unwanted folders
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
# Image Transforms
# ======================
train_transform = transforms.Compose([
    transforms.Resize((518,518)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ToTensor(),
])

test_transform = transforms.Compose([
    transforms.Resize((518,518)),
    transforms.ToTensor(),
])

# ======================
# Helper: recursive train/test split
# ======================
def create_train_test_split(dataset_root, train_ratio=0.8, max_per_class=None):
    # Move these OUTSIDE the dataset_root if possible, 
    # but if they must stay inside, we must ignore them strictly:
    train_path = os.path.join(dataset_root, "train")
    test_path = os.path.join(dataset_root, "test")
    
    # IMPORTANT: Define what folders to ignore
    ignore_list = ["train", "test", "AI_Pipeline_Results", "curriculum_resources", "NeuralNetDevelopment"]

    os.makedirs(train_path, exist_ok=True)
    os.makedirs(test_path, exist_ok=True)

    # Detect class folders (ignore the ignore_list & hidden folders)
    classes = [d for d in os.listdir(dataset_root)
               if os.path.isdir(os.path.join(dataset_root,d)) 
               and not d.startswith('.') 
               and d not in ignore_list]
    for cls in classes:
        cls_root = os.path.join(dataset_root, cls)
        # Recursively collect all valid images
        imgs = []
        for dirpath, _, files in os.walk(cls_root):
            if any(part.startswith('.') or part in ["train","test"] for part in dirpath.split(os.sep)):
                continue  # skip hidden and train/test folders
            for f in files:
                if f.lower().endswith(('.jpg','.jpeg','.png','.tif','.tiff')):
                    imgs.append(os.path.join(dirpath, f))
                    print("Traversing:", os.path.join(dirpath, f))

        if not imgs:
            print(f"Warning: No images found for class {cls}, skipping.")
            continue

        # Limit images per class for quick testing
        if max_per_class is not None:
            imgs = imgs[:max_per_class]

        n_train = int(len(imgs) * train_ratio)
        train_imgs = imgs[:n_train]
        test_imgs = imgs[n_train:]

        # Create class folders in train/test
        train_cls_folder = os.path.join(train_path, cls)
        test_cls_folder = os.path.join(test_path, cls)
        os.makedirs(train_cls_folder, exist_ok=True)
        os.makedirs(test_cls_folder, exist_ok=True)

        # Copy images
        for f in train_imgs:
            shutil.copy(f, os.path.join(train_cls_folder, os.path.basename(f)))
        for f in test_imgs:
            shutil.copy(f, os.path.join(test_cls_folder, os.path.basename(f)))

    print("Train/test split created at:", train_path, test_path)
    
    return train_path, test_path

# ======================
# Train classifier
# ======================
def train_disease_classifier(dataset_root,
                             batch_size=32,
                             epochs_head=5,
                             epochs_fine=3,
                             save_path="week8_dinov2_finetuned.pth",
                             max_per_class=None):
    if os.path.exists(os.path.join(dataset_root, "train")):
        shutil.rmtree(os.path.join(dataset_root, "train"))
        shutil.rmtree(os.path.join(dataset_root, "test"))
    
    # 1. First, create the physical folders and copy images
    train_path, test_path = create_train_test_split(dataset_root, max_per_class=max_per_class)

    # 2. Filter out empty folders
    def filter_non_empty(folder):
        return [d for d in os.listdir(folder)
                if os.path.isdir(os.path.join(folder, d))
                and os.listdir(os.path.join(folder, d))]

    non_empty_train = filter_non_empty(train_path)
    non_empty_test = filter_non_empty(test_path)
    
    if not non_empty_train:
        raise RuntimeError(f"No valid images found in {train_path}. Check if create_train_test_split actually copied files.")

    # 3. NOW define the datasets (Only now can you reference train_dataset)
    train_dataset = datasets.ImageFolder(root=train_path, transform=train_transform)
    test_dataset = datasets.ImageFolder(root=test_path, transform=test_transform)

    # 4. NOW you can use the debug prints
    class_names = train_dataset.classes
    num_classes = len(class_names)
    print(f"DEBUG: Found {len(train_dataset)} images in {num_classes} classes.")
    print("Classes:", class_names)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader  = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    class_names = train_dataset.classes
    num_classes = len(class_names)
    print("Classes:", class_names)

    # Load DINOv2
    model = timm.create_model("vit_base_patch14_dinov2.lvd142m", pretrained=True)

    # Freeze backbone
    for param in model.parameters():
        param.requires_grad = False

    # FIX: Get features from num_features instead of model.head
    in_features = model.num_features 
    model.head = nn.Linear(in_features, num_classes)

    model = model.to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.head.parameters(), lr=0.001)

    # Train head
    print("\nTraining classifier head...\n")
    for epoch in range(epochs_head):
        model.train()
        running_loss = 0
        for images, labels in train_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        print(f"Epoch {epoch+1}/{epochs_head}, Loss: {running_loss:.4f}")

    # Fine-tune last transformer block
    print("\nFine-tuning last transformer block...\n")
    for param in model.blocks[-1].parameters():
        param.requires_grad = True
    optimizer = optim.Adam(model.parameters(), lr=1e-5)
    for epoch in range(epochs_fine):
        model.train()
        running_loss = 0
        for images, labels in train_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        print(f"Fine Epoch {epoch+1}/{epochs_fine}, Loss: {running_loss:.4f}")

    print("Fine-tuning complete!")

    # Evaluate
    model.eval()
    all_preds, all_labels = [], []
    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            outputs = model(images)
            preds = torch.argmax(outputs, dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    accuracy = np.mean(np.array(all_preds) == np.array(all_labels))
    print(f"\nTest Accuracy: {accuracy:.4f}")
    print(classification_report(all_labels, all_preds, target_names=class_names))

    # Save
    torch.save({"model_state": model.state_dict(), "class_names": class_names}, save_path)
    print("Model saved successfully at", save_path)

# ======================
# Inference
# ======================
def classify_disease(image_path, model_path="week8_dinov2_finetuned.pth"):
    checkpoint = torch.load(model_path, map_location=DEVICE)
    class_names = checkpoint["class_names"]
    num_classes = len(class_names)
    
    # Match the model architecture used in training
    model = timm.create_model("vit_base_patch14_dinov2.lvd142m", pretrained=False)
    
    # Fix the head logic to match training
    in_features = model.num_features 
    model.head = nn.Linear(in_features, num_classes)
    
    model.load_state_dict(checkpoint["model_state"])
    model = model.to(DEVICE).eval()
    
    # Match the training resolution (518x518)
    transform = transforms.Compose([
        transforms.Resize((518, 518)), 
        transforms.ToTensor()
    ])
    
    img = Image.open(image_path).convert("RGB")
    img = transform(img).unsqueeze(0).to(DEVICE)
    
    with torch.no_grad():
        output = model(img)
        pred = torch.argmax(output, dim=1).item()
        
    return class_names[pred]

# ======================
# Standalone run
# ======================
if __name__ == "__main__":
    DATASET_ROOT = "/fs/ess/PAS2699/AI_Presidency_Dataset_CSG/Soybeans/Soybeans"
    train_disease_classifier(DATASET_ROOT, max_per_class=2)  # limit for quick testing