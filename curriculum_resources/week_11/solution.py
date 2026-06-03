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
            _attn_implementation="flash_attention_2" # use flash-attention if hardware supports
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
    You are an expert assistant for the following project:
    {config.project.context_statement}
    Domain: {config.project.domain}

    The specialized classification model has analyzed this image and concluded: {predicted_class}.

    User question: {question}

    """

    return context.strip()


# ---------------------
# Global Run Batch
# ----------------------
def run_batch(image_paths, config, stage=None, previous_results_list=None):
    device = config.execution.device
    model, processor = get_vlm_model(device)
    question = stage.prompt if stage and stage.prompt else "Describe the image."
    
    batch_outputs = []
    
    # Loop through the batch
    for i, img_path in enumerate(image_paths):
        # Get the exact data for this specific image
        predicted_class = previous_results_list[i].get("predicted_class", "Unknown")
        full_prompt = build_context(config, predicted_class, question)
        
        messages = [{"role": "user", "content": f"<|image_1|>\n{full_prompt}"}]
        prompt_text = processor.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        
        # Load the segmented image (or fallback to original)
        target_image_path = previous_results_list[i].get("segmented_image", img_path)
        img = Image.open(target_image_path).convert("RGB")
        
        # Process single image
        inputs = processor(prompt_text, [img], return_tensors="pt").to(device)
        
        # Generate single answer
        with torch.no_grad():
            generate_ids = model.generate(
                **inputs, 
                max_new_tokens=stage.max_tokens if hasattr(stage, 'max_tokens') else 50,
                temperature=0.0, 
                do_sample=False,
                eos_token_id=processor.tokenizer.eos_token_id
            )
            
        # Decode
        generate_ids = generate_ids[:, inputs['input_ids'].shape[1]:]
        answer = processor.batch_decode(generate_ids, skip_special_tokens=True)[0]
        
        metric_name = stage.target_metric if stage and stage.target_metric else "vlm_answer"
        batch_outputs.append({metric_name: answer.strip()})
        
    return batch_outputs
