"""
Week 8 - Transfer Learning with DINOv3
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import timm

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

DATA_DIR = "dataset_root"
BATCH_SIZE = 32
EPOCHS = 5

# ======================
# Data Transforms
# ======================

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

train_dataset = datasets.ImageFolder(
    root=f"{DATA_DIR}/train",
    transform=transform
)

test_dataset = datasets.ImageFolder(
    root=f"{DATA_DIR}/test",
    transform=transform
)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

num_classes = len(train_dataset.classes)

# ======================
# Load Pretrained DINOv3
# ======================

model = timm.create_model(
    "vit_base_patch16_224.dinov3",
    pretrained=True
)

# Freeze backbone
for param in model.parameters():
    param.requires_grad = False

# Replace classifier head
in_features = model.head.in_features
model.head = nn.Linear(in_features, num_classes)

model = model.to(DEVICE)

# ======================
# Training Setup
# ======================

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.head.parameters(), lr=0.001)

# ======================
# Training Loop
# ======================

for epoch in range(EPOCHS):

    model.train()
    running_loss = 0.0

    for images, labels in train_loader:

        images = images.to(DEVICE)
        labels = labels.to(DEVICE)

        optimizer.zero_grad()

        outputs = model(images)
        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        running_loss += loss.item()

    print(f"Epoch {epoch+1}/{EPOCHS}, Loss: {running_loss:.4f}")

print("Training complete!")