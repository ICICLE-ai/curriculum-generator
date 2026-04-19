"""
WEEK 14 STARTER CODE
Web Interface Optimization & Simple Usability Testing
"""

import gradio as gr
from PIL import Image
import torch
import torchvision.transforms as transforms
import torchvision.models as models

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
    model = models.resnet18(pretrained=False)
    model.fc = torch.nn.Linear(model.fc.in_features, len(CLASS_NAMES))
    model.load_state_dict(torch.load(path, map_location="cpu"))
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
    damage_percent = 35  # placeholder
    recommendation = "Monitor plant condition"

    return f"Disease: {disease}\nDamage: {damage_percent}%\nRecommendation: {recommendation}"

# -----------------------------
# Gradio Interface with optimization
# -----------------------------
iface = gr.Interface(
    fn=analyze_image,
    inputs=gr.Image(type="pil"),
    outputs="text",
    title="Optimized Plant Health Dashboard",
    description="Upload a leaf image and get fast disease prediction and recommendation.",
    live=False  # disables auto-processing while dragging
)

# Launch interface
iface.launch()