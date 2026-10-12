import os
import logging
from typing import List, Optional, Tuple
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.animation import FuncAnimation, FFMpegWriter

logger = logging.getLogger(__name__)


def render_network_flow(
    stage_names: Optional[List[str]] = None,
    tensor_shapes: Optional[List[str]] = None,
    title: str = "Neural Architecture Forward Propagation",
    output_path: str = "network_flow.mp4",
    frames: int = 48,
    fps: int = 24,
) -> Tuple[str, str]:
    """
    Renders an animated forward pass progression across deep learning architecture stages.
    Domain-agnostic representation for ViT, CNN, or tabular models.
    
    Returns:
        (video_path, poster_frame_path)
    """
    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    poster_path = os.path.splitext(output_path)[0] + "_poster.png"

    stages = stage_names or [
        "Input Tensor",
        "Feature Extractor",
        "Latent Bottleneck",
        "Projection Head",
        "Logits / Predictions"
    ]
    shapes = tensor_shapes or [
        "[B, 3, 224, 224]",
        "[B, 768, 14, 14]",
        "[B, 768]",
        "[B, 256]",
        "[B, NumClasses]"
    ]
    while len(shapes) < len(stages):
        shapes.append("[B, D]")

    n_stages = len(stages)
    fig, ax = plt.subplots(figsize=(10.667, 6.0), dpi=100)
    fig.patch.set_facecolor("#0B0F19")
    ax.set_facecolor("#0B0F19")
    ax.set_xlim(-0.5, n_stages - 0.5)
    ax.set_ylim(-1.5, 2.5)
    ax.axis("off")

    ax.text(
        (n_stages - 1) / 2.0, 2.1,
        title.upper(),
        ha="center", va="center",
        color="#F8FAFC", fontsize=13, fontweight="bold"
    )

    boxes = []
    # Base layout
    for i, (stg, shp) in enumerate(zip(stages, shapes)):
        box = FancyBboxPatch(
            (i - 0.38, -0.4), 0.76, 1.2,
            boxstyle="round,pad=0.08,rounding_size=0.15",
            facecolor="#1E293B",
            edgecolor="#334155",
            linewidth=1.5
        )
        ax.add_patch(box)
        boxes.append(box)

        ax.text(
            i, 0.45, f"STAGE {i+1}",
            ha="center", va="center",
            color="#94A3B8", fontsize=8.5, fontweight="bold"
        )
        ax.text(
            i, 0.1, stg,
            ha="center", va="center",
            color="#F8FAFC", fontsize=9.5, fontweight="bold",
            wrap=True
        )
        ax.text(
            i, -0.22, shp,
            ha="center", va="center",
            color="#38BDF8", fontsize=8, fontfamily="monospace"
        )

        if i < n_stages - 1:
            ax.annotate(
                "",
                xy=(i + 0.42, 0.2), xytext=(i + 0.58, 0.2),
                arrowprops=dict(arrowstyle="->", color="#475569", lw=2, mutation_scale=14)
            )

    plt.tight_layout()
    fig.savefig(poster_path, facecolor=fig.get_facecolor(), dpi=100)

    # Animation traveling pulse across stages
    def update(frame_idx):
        active_pos = (frame_idx / float(frames)) * n_stages
        for i, box in enumerate(boxes):
            dist = abs(i - active_pos)
            if dist < 0.8:
                box.set_edgecolor("#38BDF8")
                box.set_linewidth(3.0)
                box.set_facecolor("#0F2847")
            else:
                box.set_edgecolor("#334155")
                box.set_linewidth(1.5)
                box.set_facecolor("#1E293B")
        return boxes

    anim = FuncAnimation(fig, update, frames=frames, interval=1000 / fps, blit=False)
    writer = FFMpegWriter(fps=fps, metadata=dict(artist="Smart Curriculum Designer"), extra_args=["-vcodec", "libx264", "-pix_fmt", "yuv420p"])
    anim.save(output_path, writer=writer)
    plt.close(fig)

    return output_path, poster_path


def render_attention_matrix_animation(
    matrix: Optional[np.ndarray] = None,
    tokens: Optional[List[str]] = None,
    title: str = "Self-Attention Weight Distribution",
    output_path: str = "attention_weights.mp4",
    frames: int = 48,
    fps: int = 24,
) -> Tuple[str, str]:
    """
    Renders an animated heatmap pulse of self-attention weights between visual or textual tokens.
    
    Returns:
        (video_path, poster_frame_path)
    """
    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    poster_path = os.path.splitext(output_path)[0] + "_poster.png"

    tokens = tokens or ["[CLS]", "Patch 1", "Patch 2", "Patch 3", "Patch 4", "Patch 5"]
    dim = len(tokens)

    if matrix is None:
        np.random.seed(101)
        raw = np.random.uniform(0.1, 1.0, size=(dim, dim))
        matrix = raw / raw.sum(axis=-1, keepdims=True)

    fig, ax = plt.subplots(figsize=(10.667, 6.0), dpi=100)
    fig.patch.set_facecolor("#0B0F19")
    ax.set_facecolor("#0B0F19")

    im = ax.imshow(matrix, cmap="magma", interpolation="nearest")
    ax.set_xticks(range(dim))
    ax.set_yticks(range(dim))
    ax.set_xticklabels(tokens, color="#94A3B8", fontsize=9, rotation=35, ha="right")
    ax.set_yticklabels(tokens, color="#94A3B8", fontsize=9)
    ax.set_title(title.upper(), color="#F8FAFC", fontsize=12, fontweight="bold", pad=12)

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(colors="#94A3B8", labelsize=8)
    cbar.outline.set_edgecolor("#334155")

    plt.tight_layout()
    fig.savefig(poster_path, facecolor=fig.get_facecolor(), dpi=100)

    # Dynamic temperature pulsation animation
    def update(frame_idx):
        temp = 1.0 + 0.6 * np.sin(2.0 * np.pi * frame_idx / float(frames))
        scaled = np.exp(np.log(matrix + 1e-6) / temp)
        normed = scaled / scaled.sum(axis=-1, keepdims=True)
        im.set_data(normed)
        return [im]

    anim = FuncAnimation(fig, update, frames=frames, interval=1000 / fps, blit=False)
    writer = FFMpegWriter(fps=fps, metadata=dict(artist="Smart Curriculum Designer"), extra_args=["-vcodec", "libx264", "-pix_fmt", "yuv420p"])
    anim.save(output_path, writer=writer)
    plt.close(fig)

    return output_path, poster_path

