import os
import logging
from typing import List, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


def _create_poster_frame(first_img_path: str, caption: Optional[str], output_path: str, target_size: Tuple[int, int] = (1280, 720)) -> str:
    """Creates a high-contrast 16:9 poster frame image for the video preview."""
    target_w, target_h = target_size
    canvas = Image.new("RGB", (target_w, target_h), (11, 15, 25))

    if os.path.exists(first_img_path):
        try:
            with Image.open(first_img_path) as img:
                img_rgb = img.convert("RGB")
                # Scale keeping aspect ratio
                img_rgb.thumbnail((target_w - 80, target_h - 100), Image.Resampling.LANCZOS)
                paste_x = (target_w - img_rgb.width) // 2
                paste_y = (target_h - img_rgb.height - 40) // 2 + 10
                canvas.paste(img_rgb, (paste_x, paste_y))
        except Exception as e:
            logger.warning(f"Failed to read image for poster frame {first_img_path}: {e}")

    if caption:
        draw = ImageDraw.Draw(canvas)
        draw.text((40, target_h - 50), str(caption).upper(), fill=(56, 189, 248))

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    canvas.save(output_path, "PNG")
    return output_path


def render_artifact_morph(
    image_paths: List[str],
    captions: Optional[List[str]] = None,
    output_path: str = "artifact_morph.mp4",
    duration_per_image: float = 2.0,
    transition_frames: int = 15,
    fps: int = 24,
    target_size: Tuple[int, int] = (1280, 720),
) -> Tuple[str, str]:
    """
    Renders a smooth cross-dissolve video transition between 2 or more arbitrary image artifacts.
    Works for any domain: e.g. Raw Image -> Segmentation Mask -> Grad-CAM Heatmap.
    
    Returns:
        (video_path, poster_frame_path)
    """
    import cv2
    import subprocess
    import shutil

    valid_images = [p for p in image_paths if p and os.path.exists(p)]
    if not valid_images:
        raise ValueError(f"No valid image files found among: {image_paths}")

    out_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)
    poster_path = os.path.splitext(output_path)[0] + "_poster.png"

    captions = captions or []
    while len(captions) < len(valid_images):
        captions.append(f"Stage {len(captions) + 1}")

    # Generate the poster frame
    _create_poster_frame(valid_images[0], captions[0] if captions else None, poster_path, target_size)

    # Load and normalize all images to target canvas
    target_w, target_h = target_size
    frames_base = []
    for idx, path in enumerate(valid_images):
        canvas = Image.new("RGB", (target_w, target_h), (11, 15, 25))
        try:
            with Image.open(path) as img:
                img_rgb = img.convert("RGB")
                img_rgb.thumbnail((target_w - 60, target_h - 90), Image.Resampling.LANCZOS)
                paste_x = (target_w - img_rgb.width) // 2
                paste_y = (target_h - img_rgb.height - 30) // 2
                canvas.paste(img_rgb, (paste_x, paste_y))
        except Exception as e:
            logger.warning(f"Error loading image {path}: {e}")

        # Add stage label tag
        draw = ImageDraw.Draw(canvas)
        label_text = f"[{idx+1}/{len(valid_images)}] {captions[idx].upper()}"
        draw.text((40, target_h - 45), label_text, fill=(56, 189, 248))
        frames_base.append(np.array(canvas))

    # Generate frame sequence with cross-dissolve transitions
    total_frames = []
    hold_count = max(5, int(duration_per_image * fps))

    for i in range(len(frames_base)):
        curr_frame = frames_base[i]
        next_frame = frames_base[(i + 1) % len(frames_base)]

        # Hold current image
        for _ in range(hold_count):
            total_frames.append(curr_frame)

        # Cross-dissolve into next image (if more than 1 image)
        if len(frames_base) > 1:
            for t in range(transition_frames):
                alpha = t / float(transition_frames)
                blended = ((1.0 - alpha) * curr_frame + alpha * next_frame).astype(np.uint8)
                total_frames.append(blended)

    # Write video frames
    raw_avi_path = os.path.splitext(output_path)[0] + "_temp.avi"
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    writer = cv2.VideoWriter(raw_avi_path, fourcc, fps, (target_w, target_h))

    for frame in total_frames:
        bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        writer.write(bgr)
    writer.release()

    # Convert to H.264 MP4 with ffmpeg for PowerPoint native playback
    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
    try:
        cmd = [
            ffmpeg_bin,
            "-y",
            "-i", raw_avi_path,
            "-vcodec", "libx264",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            output_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
        if res.returncode != 0:
            logger.warning(f"ffmpeg conversion warning: {res.stderr}")
            # Fall back to using opencv output if ffmpeg fails
            if os.path.exists(raw_avi_path) and not os.path.exists(output_path):
                shutil.move(raw_avi_path, output_path)
    except Exception as e:
        logger.warning(f"ffmpeg not available or failed: {e}. Keeping raw video format.")
        if os.path.exists(raw_avi_path) and not os.path.exists(output_path):
            shutil.move(raw_avi_path, output_path)
    finally:
        if os.path.exists(raw_avi_path):
            try:
                os.remove(raw_avi_path)
            except OSError:
                pass

    return output_path, poster_path

