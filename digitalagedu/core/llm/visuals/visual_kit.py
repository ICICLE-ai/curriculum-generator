import os
import hashlib
import json
import logging
from typing import List, Optional, Tuple, Dict, Any, Union
import numpy as np

from digitalagedu.core.llm.visuals.render_artifacts import render_artifact_morph as _raw_render_morph
from digitalagedu.core.llm.visuals.render_3d import (
    render_3d_surface_orbit as _raw_render_3d_surface,
    render_3d_scatter_orbit as _raw_render_3d_scatter,
)
from digitalagedu.core.llm.visuals.render_network import (
    render_network_flow as _raw_render_network_flow,
    render_attention_matrix_animation as _raw_render_attention,
)
from digitalagedu.core.llm.visuals.render_charts import (
    render_confusion_matrix as _raw_render_confusion_matrix,
    render_class_distribution as _raw_render_class_distribution,
    render_roc_curve as _raw_render_roc_curve,
)

logger = logging.getLogger(__name__)

# Default working assets directory
DEFAULT_ASSETS_DIR = os.path.abspath("./presentation_assets")


def _compute_cache_key(func_name: str, **kwargs) -> str:
    """Computes a deterministic SHA-256 cache key from function parameters."""
    normalized = {}
    for k, v in kwargs.items():
        if isinstance(v, np.ndarray):
            normalized[k] = v.shape
        elif isinstance(v, (list, tuple, dict, str, int, float, bool)) or v is None:
            normalized[k] = v
        else:
            normalized[k] = str(v)
    raw_str = f"{func_name}:" + json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:16]


class VisualKit:
    """
    Tier 1 Visual Asset Producer:
    Exposes domain-agnostic, parameterized methods that generate rich MP4 animations,
    3D orbits, architecture flows, and scientific charts.
    Includes content-hashed caching to avoid redundant rendering.
    """

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = os.path.abspath(output_dir or DEFAULT_ASSETS_DIR)
        os.makedirs(self.output_dir, exist_ok=True)

    def render_artifact_morph(
        self,
        image_paths: List[str],
        captions: Optional[List[str]] = None,
        duration_per_image: float = 2.0,
        filename: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Renders a cross-dissolve animation between 2+ image artifacts (Raw -> SAM Mask -> Grad-CAM).
        Returns (video_path, poster_path).
        """
        key = _compute_cache_key("artifact_morph", images=image_paths, captions=captions)
        fname = filename or f"artifact_morph_{key}.mp4"
        out_path = os.path.join(self.output_dir, fname)
        poster_path = os.path.splitext(out_path)[0] + "_poster.png"

        if os.path.exists(out_path) and os.path.exists(poster_path) and os.path.getsize(out_path) > 1000:
            logger.info(f"Using cached artifact morph animation: {out_path}")
            return out_path, poster_path

        return _raw_render_morph(
            image_paths=image_paths,
            captions=captions,
            output_path=out_path,
            duration_per_image=duration_per_image,
        )

    def render_3d_surface_orbit(
        self,
        surface_type: str = "loss_landscape",
        title: str = "Optimization Loss Surface Dynamics",
        elev: float = 30.0,
        frames: int = 72,
        fps: int = 24,
        filename: Optional[str] = None,
        **kwargs
    ) -> Tuple[str, str]:
        """
        Renders a 3D orbiting camera animation around a loss landscape or saddle point.
        Returns (video_path, poster_path).
        """
        key = _compute_cache_key("3d_surface", stype=surface_type, title=title, elev=elev, frames=frames)
        fname = filename or f"3d_surface_{key}.mp4"
        out_path = os.path.join(self.output_dir, fname)
        poster_path = os.path.splitext(out_path)[0] + "_poster.png"

        if os.path.exists(out_path) and os.path.exists(poster_path) and os.path.getsize(out_path) > 1000:
            logger.info(f"Using cached 3D surface animation: {out_path}")
            return out_path, poster_path

        return _raw_render_3d_surface(
            surface_type=surface_type,
            title=title,
            output_path=out_path,
            elev=elev,
            frames=frames,
            fps=fps,
        )

    def render_3d_scatter_orbit(
        self,
        points_3d: Optional[np.ndarray] = None,
        labels: Optional[List[Union[str, int]]] = None,
        title: str = "3D Latent Embedding Cluster Space",
        elev: float = 25.0,
        frames: int = 72,
        fps: int = 24,
        filename: Optional[str] = None,
        **kwargs
    ) -> Tuple[str, str]:
        """
        Renders a 3D camera orbit around latent embedding clusters (PCA/t-SNE/UMAP).
        Returns (video_path, poster_path).
        """
        key = _compute_cache_key("3d_scatter", title=title, elev=elev, frames=frames, n_pts=len(points_3d) if points_3d is not None else 0)
        fname = filename or f"3d_scatter_{key}.mp4"
        out_path = os.path.join(self.output_dir, fname)
        poster_path = os.path.splitext(out_path)[0] + "_poster.png"

        if os.path.exists(out_path) and os.path.exists(poster_path) and os.path.getsize(out_path) > 1000:
            logger.info(f"Using cached 3D scatter animation: {out_path}")
            return out_path, poster_path

        return _raw_render_3d_scatter(
            points_3d=points_3d,
            labels=labels,
            title=title,
            output_path=out_path,
            elev=elev,
            frames=frames,
            fps=fps,
        )

    def render_network_flow(
        self,
        stage_names: Optional[List[str]] = None,
        tensor_shapes: Optional[List[str]] = None,
        title: str = "Neural Architecture Forward Propagation",
        frames: int = 48,
        fps: int = 24,
        filename: Optional[str] = None,
        **kwargs
    ) -> Tuple[str, str]:
        """
        Renders an animated forward pass pulse across deep learning architecture blocks.
        Returns (video_path, poster_path).
        """
        key = _compute_cache_key("network_flow", stages=stage_names, shapes=tensor_shapes, title=title, frames=frames)
        fname = filename or f"network_flow_{key}.mp4"
        out_path = os.path.join(self.output_dir, fname)
        poster_path = os.path.splitext(out_path)[0] + "_poster.png"

        if os.path.exists(out_path) and os.path.exists(poster_path) and os.path.getsize(out_path) > 1000:
            logger.info(f"Using cached network flow animation: {out_path}")
            return out_path, poster_path

        return _raw_render_network_flow(
            stage_names=stage_names,
            tensor_shapes=tensor_shapes,
            title=title,
            frames=frames,
            fps=fps,
            output_path=out_path,
        )

    def render_attention_matrix_animation(
        self,
        matrix: Optional[np.ndarray] = None,
        tokens: Optional[List[str]] = None,
        title: str = "Self-Attention Weight Distribution",
        frames: int = 48,
        fps: int = 24,
        filename: Optional[str] = None,
        **kwargs
    ) -> Tuple[str, str]:
        """
        Renders an animated heatmap pulse of self-attention weights.
        Returns (video_path, poster_path).
        """
        key = _compute_cache_key("attention_matrix", title=title, tokens=tokens, frames=frames)
        fname = filename or f"attention_matrix_{key}.mp4"
        out_path = os.path.join(self.output_dir, fname)
        poster_path = os.path.splitext(out_path)[0] + "_poster.png"

        if os.path.exists(out_path) and os.path.exists(poster_path) and os.path.getsize(out_path) > 1000:
            logger.info(f"Using cached attention matrix animation: {out_path}")
            return out_path, poster_path

        return _raw_render_attention(
            matrix=matrix,
            tokens=tokens,
            title=title,
            frames=frames,
            fps=fps,
            output_path=out_path,
        )

    def render_confusion_matrix(
        self,
        confusion_dict: Optional[Dict[str, Dict[str, int]]] = None,
        classes: Optional[List[str]] = None,
        title: str = "Empirical Pipeline Confusion Matrix",
        filename: Optional[str] = None,
    ) -> str:
        """
        Renders a diagnostic confusion matrix from telemetry. Returns image_path.
        """
        key = _compute_cache_key("confusion_matrix", conf=confusion_dict, classes=classes, title=title)
        fname = filename or f"confusion_matrix_{key}.png"
        out_path = os.path.join(self.output_dir, fname)

        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            return out_path

        return _raw_render_confusion_matrix(
            confusion_dict=confusion_dict,
            classes=classes,
            title=title,
            output_path=out_path,
        )

    def render_class_distribution(
        self,
        class_counts: Optional[Dict[str, int]] = None,
        title: str = "Dataset Class Balance & Distribution",
        filename: Optional[str] = None,
    ) -> str:
        """
        Renders a bar chart of class counts. Returns image_path.
        """
        key = _compute_cache_key("class_dist", counts=class_counts, title=title)
        fname = filename or f"class_distribution_{key}.png"
        out_path = os.path.join(self.output_dir, fname)

        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            return out_path

        return _raw_render_class_distribution(
            class_counts=class_counts,
            title=title,
            output_path=out_path,
        )

    def render_roc_curve(
        self,
        auc_score: float = 0.97,
        title: str = "ROC-AUC Diagnostic Evaluation Curve",
        filename: Optional[str] = None,
    ) -> str:
        """
        Renders an ROC curve from empirical AUC score. Returns image_path.
        """
        key = _compute_cache_key("roc_curve", auc=round(float(auc_score), 4), title=title)
        fname = filename or f"roc_curve_{key}.png"
        out_path = os.path.join(self.output_dir, fname)

        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            return out_path

        return _raw_render_roc_curve(
            auc_score=auc_score,
            title=title,
            output_path=out_path,
        )

    class Colors:
        """Modern high-contrast color constants for custom matplotlib scripts."""
        BG = "#0B0F19"
        CARD = "#1E293B"
        BORDER = "#334155"
        TEXT = "#F8FAFC"
        MUTED = "#94A3B8"
        CYAN = "#38BDF8"
        INDIGO = "#6366F1"
        EMERALD = "#10B981"
        CORAL = "#EF4444"
        GOLD = "#F59E0B"
        PURPLE = "#A855F7"

    def create_figure(
        self,
        width: float = 8.0,
        height: float = 4.8,
        title: Optional[str] = None,
        dark_mode: bool = True
    ) -> Tuple[Any, Any]:
        """
        Creates a styled matplotlib (fig, ax) pre-configured with the presentation's design system.
        """
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(width, height), dpi=150)
        bg = self.Colors.BG if dark_mode else "#FFFFFF"
        card = self.Colors.CARD if dark_mode else "#F8FAFC"
        text = self.Colors.TEXT if dark_mode else "#0F172A"
        muted = self.Colors.MUTED if dark_mode else "#64748B"
        border = self.Colors.BORDER if dark_mode else "#E2E8F0"

        fig.patch.set_facecolor(bg)
        ax.set_facecolor(card)
        ax.tick_params(colors=muted, labelsize=10)
        for spine in ax.spines.values():
            spine.set_color(border)
            spine.set_linewidth(1.2)
        ax.grid(True, linestyle="--", alpha=0.25, color=muted)
        if title:
            ax.set_title(title, color=text, fontsize=13, fontweight="bold", pad=12)
        return fig, ax

    def save_figure(
        self,
        fig: Any,
        filename: Optional[str] = None,
        dpi: int = 150
    ) -> str:
        """
        Saves a matplotlib figure cleanly to the output directory with tight layout.
        Returns the saved absolute image file path.
        """
        import matplotlib.pyplot as plt
        import uuid
        fname = filename or f"custom_visual_{uuid.uuid4().hex[:8]}.png"
        if not fname.endswith(".png"):
            fname += ".png"
        out_path = os.path.join(self.output_dir, fname)
        fig.tight_layout()
        fig.savefig(out_path, dpi=dpi, facecolor=fig.get_facecolor(), edgecolor="none", bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Saved custom graphic: {out_path}")
        return out_path


# Singleton instance for easy top-level access
visual_kit = VisualKit()
