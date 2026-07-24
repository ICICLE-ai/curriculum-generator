"""
Visual XAI (Self-Attention & Grad-CAM)
Takes DINOv2's CLS to create the maps
"""

import os
import cv2
import torch
import torch.nn as nn
import numpy as np
from PIL import Image
from torchvision import transforms

def extract_attention(model, x_tensor, target_size=(518,518)):
    """ Extracts the [CLS] token self-attention matrix safely """
    attentions = []
    
    def hook_fn(module, input, output):
        attentions.append(output)

    # Clean target extraction targeting the attention layer module directly
    attn_module = model.blocks[-1].attn
    if hasattr(attn_module, 'attn_drop'):
        handle = attn_module.attn_drop.register_forward_hook(hook_fn)
    else:
        handle = attn_module.register_forward_hook(hook_fn)

    with torch.no_grad():
        _ = model(x_tensor)
    handle.remove()

    if not attentions:
        raise RuntimeError("Failed to capture attention weights.")

    attn = attentions[0]
    
    # Process 4D Attention Weights Matrix
    if attn.ndim == 4:
        cls_attn = attn[:, :, 0, 1:].mean(dim=1)  # Average across heads
        grid_size = int(np.sqrt(cls_attn.shape[-1]))
        attn_map = cls_attn[0].reshape(grid_size, grid_size).detach().cpu().numpy()
    # Process 3D Fallback Activations Matrix safely
    elif attn.ndim == 3:
        cls_token = attn[:, 0:1, :]
        patch_tokens = attn[:, 1:, :]
        cls_norm = torch.nn.functional.normalize(cls_token, dim=-1)
        patch_norm = torch.nn.functional.normalize(patch_tokens, dim=-1)
        cls_attn_tensor = (cls_norm * patch_norm).sum(dim=-1)
        grid_size = int(np.sqrt(cls_attn_tensor.shape[-1]))
        attn_map = cls_attn_tensor[0].reshape(grid_size, grid_size).detach().cpu().numpy()
    else:
        raise ValueError(f"Unexpected attention tensor dimension: {attn.ndim}")

    # Fix DINOv2 top-left attention sink
    attn_map[0, 0] = np.median(attn_map)

    denom = attn_map.max() - attn_map.min()
    if denom > 1e-8:
        attn_map = (attn_map - attn_map.min()) / denom
    else:
        attn_map = np.zeros_like(attn_map)

    return cv2.resize(attn_map, target_size)

def extract_gradcam(model, x_tensor, target_class_idx, target_size=(518,518)):
    """ Computes stable Grad-CAM activations avoiding inline forward/backward race states """
    gradients = []
    activations = []

    def forward_hook(module, input, output):
        # Save forward feature maps
        activations.append(output)

    def backward_hook(module, grad_input, grad_output):
        # Save incoming gradients relative to features
        gradients.append(grad_output[0])

    target_layer = model.blocks[-1]
    f_handle = target_layer.register_forward_hook(forward_hook)
    b_handle = target_layer.register_full_backward_hook(backward_hook)

    model.zero_grad()
    x_tensor = x_tensor.detach().clone().requires_grad_(True)
    outputs = model(x_tensor)
    
    score = outputs[0, target_class_idx]
    score.backward()
    
    f_handle.remove()
    b_handle.remove()

    if not gradients or not activations:
        return np.zeros(target_size, dtype=np.float32)

    # Detach tensors safely and isolate from execution graph
    grads = gradients[0].detach().cpu().numpy()[0] 
    acts = activations[0].detach().cpu().numpy()[0] 

    patch_grads = grads[1:, :]
    patch_acts = acts[1:, :]

    # Standard ViT Grad-CAM Math
    weights = np.mean(patch_grads, axis=0)
    cam = np.sum(patch_acts * weights, axis=-1)
    cam = np.maximum(cam, 0)

    grid_size = int(np.sqrt(len(cam)))
    cam_2d = cam.reshape(grid_size, grid_size)

    # Suppress top-left spatial patch spike artifact
    if cam_2d[0, 0] > 3 * np.percentile(cam_2d, 95):
        cam_2d[0, 0] = np.median(cam_2d)

    denom = cam_2d.max() - cam_2d.min()
    if denom > 1e-8:
        cam_normalized = (cam_2d - cam_2d.min()) / denom
    else:
        cam_normalized = np.zeros_like(cam_2d)

    return cv2.resize(cam_normalized, target_size)

def generate_heatmap_overlay(orig_img_path, heatmap, target_size = (518, 518)):
    orig_img = cv2.imread(orig_img_path)
    orig_img = cv2.resize(orig_img, target_size)
    heatmap_uint8 = np.uint8(255 * heatmap)
    colored_heatmap = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    return cv2.addWeighted(orig_img, 0.6, colored_heatmap, 0.4, 0)

def run_batch(image_paths, config, stage=None, previous_results_list=None):
    device = config.execution.device
    output_dir = config.output.directory

    attention_dir = os.path.join(output_dir, "images", "attention")
    gradcam_dir = os.path.join(output_dir, "images", "gradcam")
    os.makedirs(attention_dir, exist_ok=True)
    os.makedirs(gradcam_dir, exist_ok=True)

    from curriculum_resources.week_08.solution import get_dino_model
    model_path = stage.model_path
    model, class_names = get_dino_model(model_path, device)
    
    if model is None:
        return [{"xai_status": "Skipped (No model loaded)"} for _ in image_paths]
    
    model.eval()
    
    # Mutate fused attention flags globally before initiating loops
    if hasattr(model.blocks[-1].attn, 'fused_attn'):
        model.blocks[-1].attn.fused_attn = False

    transform = transforms.Compose([
        transforms.Resize((config.execution.image_size, config.execution.image_size)),
        transforms.ToTensor()
    ])

    batch_outputs = []
    for i, img_path in enumerate(image_paths):
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        raw_img = Image.open(img_path).convert("RGB")
        x_tensor = transform(raw_img).unsqueeze(0).to(device)

        # 1. Self-Attention Map
        attn_heatmap = extract_attention(model, x_tensor)
        attn_overlay = generate_heatmap_overlay(img_path, attn_heatmap)
        attn_save_path = os.path.join(attention_dir, f"{base_name}_attention.png")
        cv2.imwrite(attn_save_path, attn_overlay)

        # 2. Grad-CAM Map
        predicted_class_name = previous_results_list[i].get("predicted_class", "") if previous_results_list else ""
        target_cls = class_names.index(predicted_class_name) if (class_names and predicted_class_name in class_names) else 0
        
        gradcam_heatmap = extract_gradcam(model, x_tensor, target_class_idx=target_cls)
        gradcam_overlay = generate_heatmap_overlay(img_path, gradcam_heatmap)
        gradcam_save_path = os.path.join(gradcam_dir, f"{base_name}_gradcam.png")
        cv2.imwrite(gradcam_save_path, gradcam_overlay)

        batch_outputs.append({
            "attention_map_path": attn_save_path,
            "gradcam_map_path": gradcam_save_path,
            "peak_attention_intensity": float(np.max(attn_heatmap))
        })

    return batch_outputs