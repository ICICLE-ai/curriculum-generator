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
    """
    Extracts the [CLS] token self-attention matrix from DINOv2's last block
    """
    attentions = []

    def hook_fn(module, input, output):
        # Capture self-attention weights from last layer
        attentions.append(output)

    # Disable fused attention so timm executes attn_drop and exposes the attention matrix
    if hasattr(model.blocks[-1].attn, 'fused_attn'):
        model.blocks[-1].attn.fused_attn = False

    # Hook into last block attention layer's dropout (which receives the 4D softmax attention matrix)
    if hasattr(model.blocks[-1].attn, 'attn_drop'):
        handle = model.blocks[-1].attn.attn_drop.register_forward_hook(hook_fn)
    else:
        handle = model.blocks[-1].attn.register_forward_hook(hook_fn)

    with torch.no_grad():
        _ = model(x_tensor)
    
    handle.remove()

    if not attentions:
        raise RuntimeError("Failed to capture attention weights.")

    attn = attentions[0]

    # If 4D: [batch, heads, patches, patches]
    if attn.ndim == 4:
        # Extract [CLS] token attention to image patches across all heads
        cls_attn = attn[:, :, 0, 1:].mean(dim=1)  # Average across attention heads
    elif attn.ndim == 3:
        # Fallback if 3D tensor [batch, patches, embed_dim] was captured
        # Compute cosine similarity between [CLS] token and patch tokens
        cls_token = attn[:, 0:1, :]
        patch_tokens = attn[:, 1:, :]
        cls_attn = torch.cosine_similarity(cls_token, patch_tokens, dim=-1)
    else:
        raise ValueError(f"Unexpected attention tensor dimension: {attn.ndim}")

    grid_size = int(np.sqrt(cls_attn.shape[-1]))
    attn_map = cls_attn[0].reshape(grid_size, grid_size).detach().cpu().numpy()

    # Normalize to [0, 1]
    attn_map = (attn_map - attn_map.min()) / (attn_map.max() - attn_map.min() + 1e-8)
    attn_resized = cv2.resize(attn_map, target_size)

    return attn_resized

def extract_gradcam(model, x_tensor, target_class_idx, target_size=(518,518)):
    """
    Computes Grad-CAM activations for the target class logit based on DINOv2's last block
    """
    gradients = []
    activations = []

    def save_gradient(grad):
        gradients.append(grad)
    
    def hook_fn(module, input, output):
        activations.append(output)
        if output.requires_grad:
            output.register_hook(save_gradient)

    # Hook last transformer block
    handle = model.blocks[-1].register_forward_hook(hook_fn)

    # Forward pass with gradients enabled
    model.zero_grad()
    x_tensor = x_tensor.detach().clone()
    x_tensor.requires_grad = True
    outputs = model(x_tensor)

    score = outputs[0, target_class_idx]
    score.backward()

    handle.remove()

    if not gradients or not activations:
        return np.zeros(target_size, dtype=np.float32)

    grads = gradients[0].detach().cpu().numpy()[0]
    acts = activations[0].detach().cpu().numpy()[0]

    # Exclude CLS token (index 0) and use patch tokens (indices 1:)
    patch_grads = grads[1:, :]
    patch_acts = acts[1:, :]

    # Global average pooling on patch gradients to compute channel importance weights
    weights = np.mean(patch_grads, axis=0)

    # Weighted sum over channel features for each spatial patch
    cam = np.dot(patch_acts, weights)

    # Apply ReLU (keep positive activations)
    cam = np.maximum(cam, 0)

    # Reshape 1D patch activations into 2D spatial grid
    grid_size = int(np.sqrt(len(cam)))
    cam_2d = cam.reshape(grid_size, grid_size)

    # Normalize map to [0, 1]
    cam_normalized = (cam_2d - cam_2d.min()) / (cam_2d.max() - cam_2d.min() + 1e-8)
    cam_resized = cv2.resize(cam_normalized, target_size)
    return cam_resized

def generate_heatmap_overlay(orig_img_path, heatmap, target_size = (518, 518)):
    """
    Blends original RGB image with OpenCV JET colormap
    """
    orig_img = cv2.imread(orig_img_path)
    orig_img = cv2.resize(orig_img, target_size)

    heatmap_uint8 = np.uint8(255 * heatmap)
    colored_heatmap = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

    # Blend original image and heatmap
    overlay = cv2.addWeighted(orig_img, 0.6, colored_heatmap, 0.4, 0)
    return overlay

def run_batch(image_paths, config, stage=None, previous_results_list=None):
    """
    Pipeline Entry Point for XAI.
    """
    device = config.execution.device
    output_dir = config.output.directory
    
    # Create two separate subdirectories for attention and gradcam
    attention_dir = os.path.join(output_dir, "images", "attention")
    gradcam_dir = os.path.join(output_dir, "images", "gradcam")
    os.makedirs(attention_dir, exist_ok=True)
    os.makedirs(gradcam_dir, exist_ok=True)

    # Re-use classification model or load from checkpoint
    from curriculum_resources.week_08.solution import get_dino_model
    model_path = stage.model_path

    model, class_names = get_dino_model(model_path, device)

    if model is None:
        return [{"xai_status": "Skipped (No model loaded)"} for _ in image_paths]

    model.eval()

    transform = transforms.Compose([
        transforms.Resize((config.execution.image_size, config.execution.image_size)),
        transforms.ToTensor()
    ])

    batch_outputs = []

    for i, img_path in enumerate(image_paths):
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        
        raw_img = Image.open(img_path).convert("RGB")
        x_tensor = transform(raw_img).unsqueeze(0).to(device)

        # 1. Extract & Save Self-Attention Map (to images/attention/)
        attn_heatmap = extract_attention(model, x_tensor)
        attn_overlay = generate_heatmap_overlay(img_path, attn_heatmap)
        attn_save_path = os.path.join(attention_dir, f"{base_name}_attention.png")
        cv2.imwrite(attn_save_path, attn_overlay)

        # 2. Extract & Save Grad-CAM Map (to images/gradcam/)
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