"""
WEEK 11 FINAL SOLUTION
Qwen2-VL Plant Disease QA (Pipeline Ready)
"""

import torch
from PIL import Image
from qwen import QwenForVision2Seq, QwenProcessor

MODEL_NAME = "Qwen/Qwen2-VL-2B-Instruct"

processor = QwenProcessor.from_pretrained(MODEL_NAME)
model = QwenForVision2Seq.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    device_map="auto"
)
# ----------------------------
# Config
# ----------------------------

MODEL_NAME = "Qwen/Qwen2-VL-2B-Instruct"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print("Loading Qwen2-VL model...")

processor = AutoProcessor.from_pretrained(MODEL_NAME)

model = AutoModelForVision2Seq.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
    device_map="auto"
)

model.eval()

print("Qwen2-VL loaded successfully")


# ----------------------------
# Build Context
# ----------------------------

def build_context(disease, damage, question):

    context = f"""
You are an agricultural plant pathology assistant.

Crop: Soybean
Disease detected: {disease}
Estimated leaf damage: {damage} percent

User question: {question}

Provide a short, practical answer for a farmer.
"""

    return context


# ----------------------------
# Ask VLM
# ----------------------------

def ask_vlm(image_path, disease, damage, question):

    image = Image.open(image_path).convert("RGB")

    prompt = build_context(disease, damage, question)

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt}
            ]
        }
    ]

    text = processor.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = processor(
        text=[text],
        images=[image],
        return_tensors="pt"
    ).to(model.device)

    with torch.no_grad():

        output_ids = model.generate(
            **inputs,
            max_new_tokens=128,
            temperature=0.3,
            top_p=0.9
        )

    answer = processor.batch_decode(
        output_ids,
        skip_special_tokens=True
    )[0]

    return answer.strip()