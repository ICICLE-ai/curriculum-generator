import os
import logging
from typing import Optional, Union
from pptx.util import Pt, Length
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN

from digitalagedu.core.llm.slide_kit.theme import (
    Theme,
    _to_length,
    _clamp_bounds,
)
from digitalagedu.core.llm.slide_kit.cards import add_card

logger = logging.getLogger(__name__)


def add_video(
    slide,
    x: Union[int, float, Length],
    y: Union[int, float, Length],
    w: Union[int, float, Length],
    h: Union[int, float, Length],
    video_path: str,
    poster_image_path: Optional[str] = None,
    title: Optional[str] = None,
    *args,
    **kwargs
):
    """
    Embeds an MP4 video into the PowerPoint slide with a poster frame preview image.
    Uses H.264 video format compatible with native PowerPoint playback.
    """
    vid_file = video_path or kwargs.get("movie_path") or kwargs.get("path")
    if not vid_file or not os.path.exists(vid_file):
        logger.warning(f"Video file not found: {vid_file}. Skipping add_video.")
        return None

    poster = poster_image_path or kwargs.get("poster") or kwargs.get("poster_frame")
    if not poster:
        auto_poster = os.path.splitext(vid_file)[0] + "_poster.png"
        if os.path.exists(auto_poster):
            poster = auto_poster

    lx, ly, lw, lh = _clamp_bounds(x, y, w, h)

    # Optional border card frame
    frame = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        lx - _to_length(0.06), ly - _to_length(0.06),
        lw + _to_length(0.12), lh + _to_length(0.12)
    )
    frame.fill.solid()
    frame.fill.fore_color.rgb = Theme.CARD_BG
    frame.line.color.rgb = Theme.ACCENT_CYAN
    frame.line.width = Pt(1.5)

    movie = slide.shapes.add_movie(
        vid_file,
        lx, ly, lw, lh,
        poster_frame_image=poster if poster and os.path.exists(poster) else None,
        mime_type="video/mp4"
    )
    return movie


def add_image(
    slide,
    x: Union[int, float, Length],
    y: Union[int, float, Length],
    w: Union[int, float, Length],
    h: Union[int, float, Length],
    image_path: str,
    title: Optional[str] = None,
    caption: Optional[str] = None,
    *args,
    **kwargs
):
    """
    Embeds an image into the slide with an optional title pill and bottom caption.
    """
    img_file = image_path or kwargs.get("path") or kwargs.get("file")
    if not img_file or not os.path.exists(img_file):
        # Render a stylish placeholder card rather than failing or logging fatal warnings
        placeholder_title = title or caption or "Visual Artifact"
        return add_card(
            slide, x, y, w, h,
            title=placeholder_title,
            body=f"[Asset Placeholder: {os.path.basename(str(img_file or 'visual'))}]",
            accent_color=Theme.ACCENT_CYAN
        )

    lx, ly, lw, lh = _clamp_bounds(x, y, w, h)

    # Background card frame
    frame = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        lx - _to_length(0.05), ly - _to_length(0.05),
        lw + _to_length(0.1), lh + _to_length(0.1)
    )
    frame.fill.solid()
    frame.fill.fore_color.rgb = Theme.CARD_BG
    frame.line.color.rgb = Theme.CARD_BORDER
    frame.line.width = Pt(1.2)

    pic = slide.shapes.add_picture(img_file, lx, ly, lw, lh)

    if title or caption:
        cap_text = title or caption
        tbox = slide.shapes.add_textbox(
            lx, ly + lh - _to_length(0.4),
            lw, _to_length(0.4)
        )
        tf = tbox.text_frame
        p = tf.paragraphs[0]
        p.text = str(cap_text)
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = Theme.ACCENT_CYAN
        p.alignment = PP_ALIGN.CENTER

    return pic


def add_artifact_comparison(
    slide,
    x: Union[int, float, Length],
    y: Union[int, float, Length],
    w: Union[int, float, Length],
    h: Union[int, float, Length],
    original_path: str,
    processed_path: str,
    original_label: str = "ORIGINAL INPUT",
    processed_label: str = "PROCESSED ARTIFACT",
    *args,
    **kwargs
):
    """
    Renders side-by-side artifact comparison cards (e.g. Raw image vs SAM mask / Grad-CAM).
    """
    lx, ly, lw, lh = _to_length(x), _to_length(y), _to_length(w), _to_length(h)
    gap = _to_length(0.3)
    col_w = (lw - gap) / 2.0

    # Column 1
    add_card(slide, lx, ly, col_w, lh, title=original_label, title_size=10)
    if os.path.exists(original_path):
        add_image(slide, lx + _to_length(0.2), ly + _to_length(0.5), col_w - _to_length(0.4), lh - _to_length(0.7), original_path)

    # Column 2
    add_card(slide, lx + col_w + gap, ly, col_w, lh, title=processed_label, accent_color=Theme.ACCENT_EMERALD, title_size=10)
    if os.path.exists(processed_path):
        add_image(slide, lx + col_w + gap + _to_length(0.2), ly + _to_length(0.5), col_w - _to_length(0.4), lh - _to_length(0.7), processed_path)

