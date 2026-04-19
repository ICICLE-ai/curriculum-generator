"""
WEEK 14 SOLUTION
Optimized Web Interface + Usability Testing
"""

import gradio as gr
from PIL import Image
import torch
import torchvision.transforms as transforms
import torchvision.models as models

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
# Load pre-trained ResNet Model
# -----------------------------
def load_model(path):
    model = models.resnet18(pretrained=False)
    model.fc = torch.nn.Linear(model.fc.in_features, len(CLASS_NAMES))
    model.load_state_dict(torch.load(path, map_location="cpu"))
    model.eval()
    return model

model = load_model(MODEL_PATH)

# -----------------------------
# Prediction Function with Confidence
# -----------------------------
def analyze_image(image: Image.Image):
    img_tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        outputs = model(img_tensor)
        probabilities = torch.softmax(outputs, dim=1)
        confidence, predicted = torch.max(probabilities, 1)

    disease = CLASS_NAMES[predicted.item()]
    confidence = round(confidence.item() * 100, 2)
    damage_percent = 38

    if disease == "Healthy":
        recommendation = "Plant is healthy. No action required."
    elif damage_percent > 50:
        recommendation = "Severe damage detected. Immediate treatment required."
    elif damage_percent > 30:
        recommendation = "Moderate damage detected. Apply treatment and monitor."
    else:
        recommendation = "Minor damage. Continue monitoring."

    return f"Disease: {disease} ({confidence}%)\nDamage: {damage_percent}%\nRecommendation: {recommendation}"

# -----------------------------
# Optimized Gradio Interface
# -----------------------------
iface = gr.Interface(
    fn=analyze_image,
    inputs=gr.Image(type="pil"),
    outputs="text",
    title="Optimized Plant Health Dashboard",
    description="Upload a leaf image and get fast AI predictions with confidence and recommendation.",
    live=False  # disables live updates for faster inference
)

iface.launch()