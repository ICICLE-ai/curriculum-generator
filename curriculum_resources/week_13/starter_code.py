"""
WEEK 13 STARTER CODE
Simple Web Dashboard for Plant Health AI
"""

import gradio as gr
from PIL import Image
import torch
import torchvision.transforms as transforms
import matplotlib.pyplot as plt

# -----------------------------
# Config
# -----------------------------
MODEL_PATH = "plant_classifier.pth"
CLASS_NAMES = [
    "Healthy",
    "FrogEyeLeafSpot",
    "SuddenDeathSyndrome",
    "BacterialBlight",
    "InsectDamage"
]

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

# -----------------------------
# Load Model
# -----------------------------
def load_model(path):
    model = torch.load(path)
    model.eval()
    return model

model = load_model(MODEL_PATH)

# -----------------------------
# Prediction Function
# -----------------------------
def analyze_image(image: Image.Image):

    img_tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        outputs = model(img_tensor)
        _, predicted = torch.max(outputs, 1)

    disease = CLASS_NAMES[predicted.item()]

    # Placeholder damage estimation
    damage_percent = 35

    # Placeholder recommendation
    if disease == "Healthy":
        recommendation = "Plant looks healthy. Keep monitoring."
    elif damage_percent > 30:
        recommendation = "High damage detected. Consider treatment."
    else:
        recommendation = "Minor damage. Monitor plant condition."

    return f"Disease: {disease}\nDamage: {damage_percent}%\nRecommendation: {recommendation}"

# -----------------------------
# Gradio Interface
# -----------------------------
iface = gr.Interface(
    fn=analyze_image,
    inputs=gr.Image(type="pil"),
    outputs="text",
    title="Plant Health AI Dashboard",
    description="Upload a leaf image and get disease prediction, estimated damage, and treatment recommendation."
)

# Launch interface
iface.launch()