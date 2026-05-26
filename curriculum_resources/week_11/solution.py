"""
WEEK 11 FINAL SOLUTION
Phi-3-vision (Pipeline Ready)
"""

import torch
from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor



# ----------------------------
# Lazy Load
# ----------------------------
MODEL_ID = "microsoft/Phi-3-vision-128k-instruct"
vlm_cache = None
processor_cache = None

def get_vlm_model(device):
    global vlm_cache, processor_cache
    if vlm_cache is None:
        print("Loadin Phi-3-Vision Model...")
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID, 
            device_map=device, 
            trust_remote_code=True, 
            torch_dtype=torch.float16, 
            _attn_implementation="eager" # use flash-attention if hardware supports
)

        processor_cache = AutoProcessor.from_pretrained(MODEL_ID, trust_remote_code=True)
        vlm_cache = model
        print("Phi-3-Vision loaded successfully")
    return vlm_cache, processor_cache


# ----------------------------
# Build Context
# ----------------------------

def build_context(config, predicted_class, question):

    context = f"""
    You are an assistant for the following project:
    {config.project.context_statement}
    Domain: {config.project.domain}

    the image classification model has predicted that the image contains:
    {predicted_class}
    User question: {question}

    Provide a short, direct answer.
    """

    return context.strip()


# ---------------------
# Global Run Stage
# ----------------------

def run_stage(image_path, config, stage=None, previous_results = None):
    device = config.execution.device

    # Get prediction from Week 8
    predicted_class = previous_results.get("predicted_class", "Unknown")

    # Build the question
    question = stage.prompt if stage and stage.prompt else ValueError("No question provided")

    full_prompt = build_context(config, predicted_class, question)
    

    # Load Image and Model
    image = Image.open(image_path).convert("RGB")
    model, processor = get_vlm_model(device)

    messages = [
        {"role": "user", "content": f"<|image_1|>\n{full_prompt}"}
    ]

    prompt = processor.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    inputs = processor(prompt, [image], return_tensors="pt").to(device)

    # Run inference 
    with torch.no_grad():
        generate_ids = model.generate(
            **inputs, 
            max_new_tokens=stage.max_tokens if hasattr(stage, 'max_tokens') else 50,
            temperature=0.0, 
            do_sample=False,
            eos_token_id=processor.tokenizer.eos_token_id
    )

    generate_ids = generate_ids[:, inputs['input_ids'].shape[1]:]
    answer = processor.batch_decode(generate_ids, skip_special_tokens=True)[0]

    # Get the CSV column name and name
    metric_name = stage.target_metric if stage and stage.target_metric else "vlm_answer"

    return {metric_name: answer.strip()}