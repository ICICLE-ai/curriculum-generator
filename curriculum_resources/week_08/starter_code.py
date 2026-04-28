"""
Week 8 - Transfer Learning with DINOv2
Classify corn diseases using a pre-trained vision model.

Your job: fill in the four TODO sections below.
Everything else (dataset splitting, evaluation, saving) is provided.
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
# (provided — no changes needed here)
# ======================
def create_train_test_split(dataset_root, train_ratio=0.8, max_per_class=None):
    train_path = os.path.join(dataset_root, "train")
    test_path  = os.path.join(dataset_root, "test")
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
    # Clean up any previous split so we start fresh
    for folder in ["train", "test"]:
        p = os.path.join(dataset_root, folder)
        if os.path.exists(p):
            shutil.rmtree(p)

    train_path, test_path = create_train_test_split(
        dataset_root, max_per_class=max_per_class
    )

    # ----------------------------------------------------------
    # TODO 1 — Define image transforms
    #
    # train_transform should:
    #   - Resize images to (518, 518)
    #   - Apply random horizontal flip
    #   - Apply random rotation of up to 10 degrees
    #   - Convert to tensor
    #
    # test_transform should:
    #   - Resize images to (518, 518)
    #   - Convert to tensor  (no augmentation for evaluation)
    # ----------------------------------------------------------
    train_transform = transforms.Compose([
        # TODO: add transforms here
    ])

    test_transform = transforms.Compose([
        # TODO: add transforms here
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

    class_names  = train_dataset.classes
    num_classes  = len(class_names)
    print(f"Found {len(train_dataset)} images across {num_classes} classes.")
    print("Classes:", class_names)

    # ----------------------------------------------------------
    # TODO 2 — Load DINOv2 and replace the classifier head
    #
    # Steps:
    #   1. Load "vit_base_patch14_dinov2.lvd142m" from timm with pretrained=True
    #   2. Freeze ALL model parameters (we only want to train the head first)
    #   3. Replace model.head with a single nn.Linear layer
    #      - input size:  model.num_features
    #      - output size: num_classes
    #   4. Move the model to DEVICE
    # ----------------------------------------------------------

    # TODO: load model, freeze backbone, replace head, move to DEVICE
    model = None  # replace this line

    criterion = nn.CrossEntropyLoss()

    # ----------------------------------------------------------
    # TODO 3 — Training loop (head only)
    #
    # Use Adam optimizer on model.head.parameters() with lr=0.001
    # Train for epochs_head epochs.
    # Each epoch:
    #   - set model to train mode
    #   - loop over train_loader batches
    #   - move images and labels to DEVICE
    #   - zero gradients, forward pass, compute loss, backward, step
    #   - accumulate running_loss and print it at the end of the epoch
    # ----------------------------------------------------------
    print("\nTraining classifier head...\n")
    optimizer = optim.Adam(model.head.parameters(), lr=0.001)

    # TODO: write the training loop for epochs_head epochs

    # ----------------------------------------------------------
    # TODO 4 — Fine-tuning loop (last transformer block + head)
    #
    # Unfreeze the last transformer block: model.blocks[-1]
    # Switch to Adam with lr=1e-5 across ALL model parameters.
    # Train for epochs_fine epochs using the same loop structure as TODO 3.
    # ----------------------------------------------------------
    print("\nFine-tuning last transformer block...\n")

    # TODO: unfreeze last block, create new optimizer, write fine-tuning loop

    print("Fine-tuning complete!")

    # ======================
    # Evaluation (provided — no changes needed)
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
# Inference (provided — no changes needed)
# ======================
def classify_disease(image_path, model_path="week8_dinov2_finetuned.pth"):
    checkpoint   = torch.load(model_path, map_location=DEVICE)
    class_names  = checkpoint["class_names"]
    num_classes  = len(class_names)

    model = timm.create_model("vit_base_patch14_dinov2.lvd142m", pretrained=False)
    in_features  = model.num_features
    model.head   = nn.Linear(in_features, num_classes)
    model.load_state_dict(checkpoint["model_state"])
    model        = model.to(DEVICE).eval()

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