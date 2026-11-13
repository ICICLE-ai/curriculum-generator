import os
import logging
from typing import Optional, Tuple, List, Union
import numpy as np

# Force headless Matplotlib Agg backend
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation, FFMpegWriter

logger = logging.getLogger(__name__)


def render_3d_surface_orbit(
    surface_type: str = "loss_landscape",
    title: str = "Optimization Loss Surface Dynamics",
    output_path: str = "3d_surface.mp4",
    frames: int = 72,
    fps: int = 24,
    elev: float = 30.0,
) -> Tuple[str, str]:
    """
    Renders an orbiting 3D camera animation of a mathematical surface (loss landscape, saddle point, or manifold).
    Domain-agnostic optimization visualization.
    
    Returns:
        (video_path, poster_frame_path)
    """
    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    poster_path = os.path.splitext(output_path)[0] + "_poster.png"

    # Generate 3D grid
    x = np.linspace(-2.5, 2.5, 60)
    y = np.linspace(-2.5, 2.5, 60)
    X, Y = np.meshgrid(x, y)

    if surface_type.lower() in ("saddle", "saddle_point"):
        # Saddle point: z = x^2 - y^2
        Z = X**2 - Y**2
        z_label = "Loss L(w)"
    elif surface_type.lower() in ("convex", "bowl"):
        # Convex bowl: z = x^2 + y^2
        Z = X**2 + Y**2
        z_label = "Convex Loss"
    else:
        # Complex multi-modal loss landscape
        R = np.sqrt(X**2 + Y**2) + 1e-5
        Z = np.sin(2.0 * R) / R + 0.15 * (X**2 + Y**2)
        z_label = "Objective Value"

    # Setup 16:9 dark canvas
    fig = plt.figure(figsize=(10.667, 6.0), dpi=100)
    fig.patch.set_facecolor("#0B0F19")
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#0B0F19")

    # Dark theme styling for axes
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor("#1E293B")
    ax.yaxis.pane.set_edgecolor("#1E293B")
    ax.zaxis.pane.set_edgecolor("#1E293B")
    ax.grid(color="#334155", linestyle="--", alpha=0.4)

    ax.tick_params(colors="#94A3B8", labelsize=8)
    ax.set_xlabel("Parameter θ₁", color="#38BDF8", fontsize=10, labelpad=8)
    ax.set_ylabel("Parameter θ₂", color="#38BDF8", fontsize=10, labelpad=8)
    ax.set_zlabel(z_label, color="#10B981", fontsize=10, labelpad=8)
    ax.set_title(title.upper(), color="#F8FAFC", fontsize=12, fontweight="bold", pad=14)

    surf = ax.plot_surface(
        X, Y, Z,
        cmap="viridis",
        edgecolor="#38BDF8",
        linewidth=0.2,
        alpha=0.88,
        antialiased=True
    )

    # Save initial poster frame
    ax.view_init(elev=elev, azim=45)
    plt.tight_layout()
    fig.savefig(poster_path, facecolor=fig.get_facecolor(), dpi=100)

    # Animation function rotating azimuth
    def update(frame_idx):
        azim = (frame_idx * (360.0 / frames)) % 360
        ax.view_init(elev=elev, azim=azim)
        return surf,

    anim = FuncAnimation(fig, update, frames=frames, interval=1000 / fps, blit=False)
    
    # Render with FFMpegWriter for H.264 MP4
    writer = FFMpegWriter(fps=fps, metadata=dict(artist="Smart Curriculum Designer"), extra_args=["-vcodec", "libx264", "-pix_fmt", "yuv420p"])
    anim.save(output_path, writer=writer)
    plt.close(fig)

    return output_path, poster_path


def render_3d_scatter_orbit(
    points_3d: Optional[np.ndarray] = None,
    labels: Optional[List[Union[str, int]]] = None,
    title: str = "3D Latent Embedding Cluster Space",
    output_path: str = "3d_scatter.mp4",
    frames: int = 72,
    fps: int = 24,
    elev: float = 25.0,
) -> Tuple[str, str]:
    """
    Renders an orbiting 3D camera animation of latent embedding clusters (PCA / t-SNE / UMAP).
    Works with arbitrary pipeline representations and class partitions.
    
    Returns:
        (video_path, poster_frame_path)
    """
    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    poster_path = os.path.splitext(output_path)[0] + "_poster.png"

    # Default synthetic cluster generator if no raw points passed
    if points_3d is None or len(points_3d) == 0:
        np.random.seed(42)
        n_per_cluster = 60
        c1 = np.random.randn(n_per_cluster, 3) * 0.45 + np.array([-1.2, -0.8, 0.5])
        c2 = np.random.randn(n_per_cluster, 3) * 0.45 + np.array([1.0, 1.2, -0.6])
        c3 = np.random.randn(n_per_cluster, 3) * 0.50 + np.array([0.2, -1.0, -1.0])
        points_3d = np.vstack([c1, c2, c3])
        labels = ["Class A"] * n_per_cluster + ["Class B"] * n_per_cluster + ["Class C"] * n_per_cluster

    unique_labels = sorted(list(set(labels))) if labels else ["Cluster"]
    palette = ["#38BDF8", "#10B981", "#F59E0B", "#EF4444", "#6366F1", "#EC4899"]
    label_to_color = {l: palette[i % len(palette)] for i, l in enumerate(unique_labels)}
    point_colors = [label_to_color[l] for l in labels] if labels else ["#38BDF8"] * len(points_3d)

    fig = plt.figure(figsize=(10.667, 6.0), dpi=100)
    fig.patch.set_facecolor("#0B0F19")
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#0B0F19")

    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor("#1E293B")
    ax.yaxis.pane.set_edgecolor("#1E293B")
    ax.zaxis.pane.set_edgecolor("#1E293B")
    ax.grid(color="#334155", linestyle="--", alpha=0.35)

    ax.tick_params(colors="#94A3B8", labelsize=8)
    ax.set_xlabel("Latent Dim 1", color="#94A3B8", fontsize=9, labelpad=8)
    ax.set_ylabel("Latent Dim 2", color="#94A3B8", fontsize=9, labelpad=8)
    ax.set_zlabel("Latent Dim 3", color="#94A3B8", fontsize=9, labelpad=8)
    ax.set_title(title.upper(), color="#F8FAFC", fontsize=12, fontweight="bold", pad=14)

    scatter = ax.scatter(
        points_3d[:, 0], points_3d[:, 1], points_3d[:, 2],
        c=point_colors,
        s=36,
        alpha=0.85,
        edgecolors="#F8FAFC",
        linewidths=0.4
    )

    # Save initial poster frame
    ax.view_init(elev=elev, azim=45)
    plt.tight_layout()
    fig.savefig(poster_path, facecolor=fig.get_facecolor(), dpi=100)

    def update(frame_idx):
        azim = (frame_idx * (360.0 / frames)) % 360
        ax.view_init(elev=elev, azim=azim)
        return scatter,

    anim = FuncAnimation(fig, update, frames=frames, interval=1000 / fps, blit=False)
    writer = FFMpegWriter(fps=fps, metadata=dict(artist="Smart Curriculum Designer"), extra_args=["-vcodec", "libx264", "-pix_fmt", "yuv420p"])
    anim.save(output_path, writer=writer)
    plt.close(fig)

    return output_path, poster_path

