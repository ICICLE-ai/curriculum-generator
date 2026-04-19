"""
WEEK 12 STARTER CODE
Unified AI Plant Health Analysis Pipeline

This script combines:
1. Disease classification
2. Leaf damage estimation
3. Segmentation visualization
4. AI-generated explanation
"""

import torch
import torchvision.transforms as transforms
from PIL import Image
import matplotlib.pyplot as plt

# -----------------------------
# Configuration
# -----------------------------

IMAGE_PATH = "test_leaf.jpg"
MODEL_PATH = "plant_classifier.pth"

CLASS_NAMES = [
    "Healthy",
    "FrogEyeLeafSpot",
    "SuddenDeathSyndrome",
    "BacterialBlight",
    "InsectDamage"
]

# -----------------------------
# Image Transform
# -----------------------------

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])


# -----------------------------
# Load Image
# -----------------------------

def load_image(path):
    image = Image.open(path).convert("RGB")
    return image


# -----------------------------
# Load Model
# -----------------------------

def load_model(path):
    model = torch.load(path)
    model.eval()
    return model


# -----------------------------
# Disease Prediction
# -----------------------------

def predict_disease(model, image):
    img_tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        outputs = model(img_tensor)
        _, predicted = torch.max(outputs, 1)

    return CLASS_NAMES[predicted.item()]


# -----------------------------
# Damage Estimation (placeholder)
# -----------------------------

def estimate_damage_percentage():
    """
    TODO:
    Replace this with segmentation output from Week 10
    """
    damage_percent = 35
    return damage_percent


# -----------------------------
# Generate Recommendation
# -----------------------------

def generate_recommendation(disease, damage):

    if disease == "Healthy":
        return "Plant looks healthy. Continue monitoring."

    if damage > 30:
        return "High damage detected. Consider treatment."

    return "Monitor plant condition."


# -----------------------------
# Main Pipeline
# -----------------------------

def analyze_plant(image_path):

    image = load_image(image_path)
    model = load_model(MODEL_PATH)

    disease = predict_disease(model, image)

    damage = estimate_damage_percentage()

    recommendation = generate_recommendation(disease, damage)

    print("\nPlant Analysis Report")
    print("----------------------")
    print("Predicted Disease:", disease)
    print("Estimated Damage:", damage, "%")
    print("Recommendation:", recommendation)

    plt.imshow(image)
    plt.title("Uploaded Leaf Image")
    plt.axis("off")
    plt.show()


# -----------------------------
# Run pipeline
# -----------------------------

analyze_plant(IMAGE_PATH)