"""
Week 8 - Transfer Learning with DINOv2
Classify corn diseases using a pre-trained vision model.
SOLUTION CODE — instructor reference only, do not share with students.
"""

from numpy.random import shuffle
import os
import shutil
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import json
from sklearn.model_selection import StratifiedKFold
import numpy as np
import timm
from PIL import Image
import random
import copy

# ---------------------------
# Lazy Load Cache
# ---------------------------
dino_cache = None
class_names_cache = None

def get_dino_model(model_path, device):
    global dino_cache, class_names_cache

    if dino_cache is None:
        print(f"Loading DINOv2 model into VRAM from {model_path}...")
        checkpoint = torch.load(model_path, map_location=device)
        class_names_cache = checkpoint["class_names"]
        num_classes = len(class_names_cache)

        # Build the model
        model = timm.create_model("vit_base_patch14_dinov2.lvd142m", pretrained=False)
        in_features = model.num_features
        model.head = nn.Linear(in_features, num_classes)

        # Load saved weights
        model.load_state_dict(checkpoint["model_state"])
        dino_cache = model.to(device).eval()
        print("DINOv2 loaded successfully.")

    return dino_cache, class_names_cache



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
def train_classifier(
    dataset_root,
    batch_size=32,
    image_size =518,
    device = "cpu",
    epochs_head=10,
    epochs_fine=5,
    save_path="week8_dinov2_finetuned.pth",
    max_per_class=None,
    seed = 42,
    output_directory = None
):

    # Lock in the seed
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    
    for folder in ["train", "test"]:
        p = os.path.join(dataset_root, folder)
        if os.path.exists(p):
            shutil.rmtree(p)

    # Transforms
    train_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ToTensor()
    ])

    val_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor()
    ])

    # Unify Dataset
    full_dataset_train = datasets.ImageFolder(root = dataset_root, transform= train_transform)

    full_dataset_val = datasets.ImageFolder(root = dataset_root, transform=val_transform)

    class_names = full_dataset_train.classes
    num_classes = len(class_names)

    # Extract labels for stratification
    targets = full_dataset_train.targets
    print(f"Found {len(full_dataset_train)} images across {num_classes} classes")

    k_folds = 5
    skf = StratifiedKFold(n_splits=k_folds, shuffle=True, random_state=seed)
    absolute_best_val_loss = float('inf')
    best_model_weights = None

    # metrics storage for each fold
    cv_metrics = {
        "accuracy": [],
        "precision": [],
        "recall": [],
        "f1": [],
    }

    # Track every prediction across all folds
    global_val_preds = []
    global_val_targets = []
    
    # Wrap model creation and training in fold loop
    for fold, (train_idx, val_idx) in enumerate(skf.split(np.zeros(len(targets)),targets)):
        print(f"\n{'='*30}")
        print(f"FOLD {fold+1}/{k_folds}")
        print(f"\n{'='*30}")

        # Create DataLoaders for the fold
        train_subset = Subset(full_dataset_train, train_idx)
        val_subset = Subset(full_dataset_val, val_idx)

        train_loader = DataLoader(train_subset, batch_size=batch_size, shuffle=True, num_workers=1, pin_memory=True)
        val_loader = DataLoader(val_subset, batch_size=batch_size, shuffle=False, num_workers=1, pin_memory=True)


        # TODO 2 SOLUTION — load DINOv2, freeze backbone, replace head
        model = timm.create_model("vit_base_patch14_dinov2.lvd142m", pretrained=True)

        for param in model.parameters():
            param.requires_grad = False

        in_features = model.num_features
        model.head  = nn.Linear(in_features, num_classes)
        model       = model.to(device)

        criterion = nn.CrossEntropyLoss()

        # TODO 3 SOLUTION — head training loop
        print("\nTraining classifier head...\n")
        optimizer = optim.Adam(model.head.parameters(), lr=0.001)

        for epoch in range(epochs_head):
            model.train()
            running_loss = 0.0
            for images, labels in train_loader:
                images, labels = images.to(device), labels.to(device)
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
        optimizer_fine = optim.Adam(model.parameters(), lr=1e-5)

        fold_best_val_loss = float('inf')
        fold_best_weights = None

        for epoch in range(epochs_fine):
            # Training Phase
            model.train()
            running_train_loss = 0.0

            for images, labels in train_loader:
                images, labels = images.to(device), labels.to(device)
                optimizer_fine.zero_grad()
                outputs = model(images)
                loss    = criterion(outputs, labels)
                loss.backward()
                optimizer_fine.step()
                running_train_loss += loss.item()
            #print(f"Fine Epoch {epoch+1}/{epochs_fine}, Loss: {running_loss:.4f}")

            avg_train_loss = running_train_loss / len(train_loader)

            # Validation Phase
            model.eval()
            running_val_loss = 0.0

            with torch.no_grad():
                for images, labels in val_loader:
                    images, labels = images.to(device), labels.to(device)
                    outputs = model(images)
                    loss = criterion(outputs, labels)
                    running_val_loss += loss.item()
            avg_val_loss = running_val_loss / len(val_loader)

            # Print both metrics
            print(f"Fold: {fold+1} | Fine Epoch {epoch+1}/{epochs_fine} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")

            # Model Checkpointing
            if avg_val_loss < fold_best_val_loss:
                fold_best_val_loss = avg_val_loss
                fold_best_weights = copy.deepcopy(model.state_dict())
                print(" --> Validation loss improved! Checkpointing model state.")

                # Evaluate for best fold

        print(f"--> Fold {fold+1} complete. Best Val Loss: {fold_best_val_loss:.4f}")
        if fold_best_val_loss < absolute_best_val_loss:
                absolute_best_val_loss = fold_best_val_loss
                best_model_weights = copy.deepcopy(fold_best_weights)
                print(f"*** New Best Model from Fold {fold+1}! ***")
        # Load the best weights for the fold
        model.load_state_dict(fold_best_weights)
        model.eval()

        fold_preds = []
        fold_targets = []

        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                preds = torch.argmax(outputs, dim=1)

                fold_preds.extend(preds.cpu().numpy())
                fold_targets.extend(labels.cpu().numpy())

        # Save to the global list
        global_val_preds.extend(fold_preds)
        global_val_targets.extend(fold_targets)

        # Calculate the metrics for the fold
        cv_metrics["accuracy"].append(accuracy_score(fold_targets, fold_preds))
        cv_metrics["precision"].append(precision_score(fold_targets, fold_preds, average="macro", zero_division=0))
        cv_metrics["recall"].append(recall_score(fold_targets, fold_preds, average="macro", zero_division=0))
        cv_metrics["f1"].append(f1_score(fold_targets, fold_preds, average="macro", zero_division=0))

    # Calculate averages
    final_cv_report = {
        "folds_data" : cv_metrics,
        "mean_accuracy" : round(float(np.mean(cv_metrics["accuracy"])), 2),
        "mean_precision" : round(float(np.mean(cv_metrics["precision"])), 2),
        "mean_recall" : round(float(np.mean(cv_metrics["recall"])), 2),
        "mean_f1" : round(float(np.mean(cv_metrics["f1"])), 2)
    }

    if output_directory:
        os.makedirs(output_directory, exist_ok=True)
        report_path = os.path.join(output_directory, "cv_report.json")
        cm_path = os.path.join(output_directory, "confusion_matrix.png")

    else:
        # Fallback just in case
        report_path = save_path.replace(".pth", "_cv_report.json")
        cm_path = save_path.replace(".pth", "_confusion_matrix.png")

    # Save the JSON report
    with open(report_path, "w") as f:
        json.dump(final_cv_report, f, indent=4)
    print(f"CV report saved to {report_path}")

    # Generate confusion matrix
    cm = confusion_matrix(global_val_targets, global_val_preds)

    plt.figure(figsize=(10,8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Global Confusion Matrix")
    
    # Save the confusion matrix
    plt.savefig(cm_path, bbox_inches="tight")
    plt.close()
    print(f"Confusion matrix saved to {cm_path}")

    print("\nAll 5 Folds Complete!")

    # Load the best weights across the folds
    model.load_state_dict(best_model_weights)
    print(f"\nLoaded best model of val loss {absolute_best_val_loss:.4f}")

    save_dir = os.path.dirname(save_path)
    if save_path:
        os.makedirs(save_dir, exist_ok=True)

        # Save the final model
        torch.save(
            {
                "model_state": model.state_dict(),
                "class_names": class_names
            },
            save_path
        )
        print(f"Model saved successfully to {save_path}")


# ======================
# Inference (Batched)
# ======================
def classify_batch(image_paths, model_path="week8_dinov2_finetuned.pth", image_size=518, device = "cpu"):
    
    # Grab model from RAM
    model, class_names = get_dino_model(model_path, device)

    # Prepare image
    transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
    ])

    # Pre-process all images into a list of tensors
    batch_tensors = []
    for img_path in image_paths:
        img = Image.open(img_path).convert("RGB")
        img_t = transform(img)
        batch_tensors.append(img_t)

    # Stack the tensors
    batch_tensor = torch.stack(batch_tensors).to(device)

    # Predict the batch
    with torch.no_grad():
        outputs = model(batch_tensor)
        preds = torch.argmax(outputs, dim=1).tolist()

    # Convert preidctions to string labels
    return [class_names[p] for p in preds]


# =================
# Global run stage
# =================
def run_batch(image_paths, config, stage=None, previous_results_list=None):
    """
    Standardized entry point for orchestrator
    """
    model_path = stage.model_path if stage and stage.model_path else "week8_dinov2_finetuned.pth"
    device = config.execution.device

    seed = config.execution.seed

    # Optional automatically train if the model doesnt exist
    if not os.path.exists(model_path):
        print(f"[{stage.name}] Model not found. Training...")
        train_classifier(
            config.dataset.root_path,
            batch_size=config.execution.batch_size,
            image_size=config.execution.image_size,
            save_path=model_path,
            max_per_class=config.execution.max_samples,
            device = device,
            seed = seed,
            output_directory = config.output.directory
        )

    # Run inference
    predicted_class = classify_batch(
        image_paths, 
        model_path=model_path,
        image_size = config.execution.image_size,
        device = device
        )

    return [{"predicted_class": pred} for pred in predicted_class]


# ======================
# Standalone run
# ======================
if __name__ == "__main__":
    DATASET_ROOT = "/fs/ess/PAS2699/AI_Presidency_Dataset_CSG/Soybeans/Soybeans"
    train_classifier(DATASET_ROOT, max_per_class=2)