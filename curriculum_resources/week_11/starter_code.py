"""
WEEK 11 STARTER CODE
Vision-Language QA using Qwen2-VL
"""

from PIL import Image

import torch
from transformers import AutoProcessor, AutoModelForVision2Seq


MODEL_NAME = "Qwen/Qwen2-VL-2B-Instruct"

processor = AutoProcessor.from_pretrained(MODEL_NAME)
model = AutoModelForVision2Seq.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    device_map="auto"
)


def ask_question(image_path, question):

    image = Image.open(image_path).convert("RGB")

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": question}
            ]
        }
    ]

    text = processor.apply_chat_template(messages, tokenize=False)

    inputs = processor(text=[text], images=[image], return_tensors="pt").to(model.device)

    output_ids = model.generate(**inputs, max_new_tokens=128)

    answer = processor.batch_decode(output_ids, skip_special_tokens=True)[0]

    return answer


if __name__ == "__main__":

    IMAGE_PATH = "segmented_leaf.png"

    question = input("Ask a question about the plant: ")

    response = ask_question(IMAGE_PATH, question)

    print("\nModel Answer:", response)