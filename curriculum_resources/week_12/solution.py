"""
WEEK 12 SOLUTION
Unified AI Plant Health Analysis Pipeline
"""

import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import matplotlib.pyplot as plt


IMAGE_PATH = "test_leaf.jpg"
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


def load_image(path):
    image = Image.open(path).convert("RGB")
    return image


def load_model(path):

    model = models.resnet18(pretrained=False)
    model.fc = torch.nn.Linear(model.fc.in_features, len(CLASS_NAMES))

    model.load_state_dict(torch.load(path, map_location="cpu"))
    model.eval()

    return model


def predict_disease(model, image):

    img_tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        outputs = model(img_tensor)
        probabilities = torch.softmax(outputs, dim=1)

        confidence, predicted = torch.max(probabilities, 1)

    disease = CLASS_NAMES[predicted.item()]
    confidence = confidence.item()

    return disease, confidence


def estimate_damage_percentage():

    """
    Placeholder for segmentation integration
    """

    damage_percent = 38

    return damage_percent


def generate_recommendation(disease, damage):

    if disease == "Healthy":
        return "Plant is healthy. No action required."

    if damage > 50:
        return "Severe damage detected. Immediate treatment recommended."

    if damage > 30:
        return "Moderate damage detected. Apply treatment and monitor."

    return "Minor damage. Continue monitoring."


def analyze_plant(image_path):

    image = load_image(image_path)
    model = load_model(MODEL_PATH)

    disease, confidence = predict_disease(model, image)

    damage = estimate_damage_percentage()

    recommendation = generate_recommendation(disease, damage)

    print("\nPlant Health Analysis")
    print("----------------------")
    print("Disease:", disease)
    print("Model Confidence:", round(confidence * 100, 2), "%")
    print("Damage:", damage, "%")
    print("Recommendation:", recommendation)

    plt.imshow(image)
    plt.title("Leaf Image")
    plt.axis("off")
    plt.show()


analyze_plant(IMAGE_PATH)