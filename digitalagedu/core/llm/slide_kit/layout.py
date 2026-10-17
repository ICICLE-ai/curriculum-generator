from typing import List, Optional, Tuple, Union
from pptx import Presentation
from pptx.util import Inches, Pt, Length
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

from digitalagedu.core.llm.slide_kit.theme import (
    Theme,
    SLIDE_WIDTH_INCHES,
    SLIDE_HEIGHT_INCHES,
    _to_length,
)
from digitalagedu.core.llm.slide_kit.cards import add_card, add_metric_card
from digitalagedu.core.llm.slide_kit.media import add_image, add_video


def create_slide(prs: Presentation, bg_color: Optional[RGBColor] = None, *args, **kwargs):
    """Creates a new blank 16:9 slide with a full-bleed solid background."""
    prs.slide_width = Inches(SLIDE_WIDTH_INCHES)
    prs.slide_height = Inches(SLIDE_HEIGHT_INCHES)
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    bg_col = bg_color or kwargs.get("bg") or kwargs.get("color") or Theme.BG_DARK
    bg = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        0, 0, Inches(SLIDE_WIDTH_INCHES), Inches(SLIDE_HEIGHT_INCHES)
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = bg_col
    bg.line.fill.background()
    return slide


def add_header(
    slide,
    tag: str = "CURRICULUM",
    title: str = "",
    subtitle: Optional[str] = None,
    tag_color: Optional[RGBColor] = None,
    *args,
    **kwargs
):
    """Adds a standardized top category pill, bold title, and optional subtitle."""
    tg = str(tag or kwargs.get("category") or kwargs.get("topic") or "CURRICULUM")
    ttl = str(title or kwargs.get("heading") or kwargs.get("title_text") or "")
    sub = subtitle or kwargs.get("sub") or kwargs.get("description")
    accent = tag_color or kwargs.get("accent") or Theme.ACCENT_CYAN
    
    # 1. Category pill
    pill_w = max(2.2, len(tg) * 0.11 + 0.5)
    pill = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        _to_length(0.8), _to_length(0.5), _to_length(pill_w), _to_length(0.38)
    )
    pill.fill.solid()
    pill.fill.fore_color.rgb = Theme.CARD_BG
    pill.line.color.rgb = accent
    pill.line.width = Pt(1.2)

    tf_pill = pill.text_frame
    tf_pill.word_wrap = False
    tf_pill.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_pill = tf_pill.paragraphs[0]
    p_pill.text = tg.upper()
    p_pill.font.size = Pt(9.5)
    p_pill.font.bold = True
    p_pill.font.color.rgb = accent
    p_pill.alignment = PP_ALIGN.CENTER

    # 2. Main title & subtitle
    tbox = slide.shapes.add_textbox(
        _to_length(0.8), _to_length(0.95), _to_length(11.733), _to_length(0.9)
    )
    tf = tbox.text_frame
    tf.word_wrap = True
    p_title = tf.paragraphs[0]
    p_title.text = ttl
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = Theme.TEXT_PRIMARY

    if sub:
        p_sub = tf.add_paragraph()
        p_sub.text = str(sub)
        p_sub.font.size = Pt(12)
        p_sub.font.color.rgb = Theme.TEXT_MUTED
        p_sub.space_before = Pt(3)


def add_hero_graphic(
    slide,
    graphic_path: Optional[str] = None,
    x: Union[int, float, Length] = 0.8,
    y: Union[int, float, Length] = 1.9,
    w: Union[int, float, Length] = 7.4,
    h: Union[int, float, Length] = 5.0,
    title: Optional[str] = None,
    caption: Optional[str] = None,
    *args,
    **kwargs
):
    """
    Places a high-prominence visual asset (custom graphic, chart, or video)
    on the slide canvas with coordinate safety clamping.
    """
    actual_path = graphic_path or kwargs.get("path") or kwargs.get("image_path") or kwargs.get("graphic")
    if actual_path and str(actual_path).endswith(".mp4"):
        return add_video(slide, x, y, w, h, video_path=actual_path, title=title, *args, **kwargs)
    return add_image(slide, x, y, w, h, image_path=actual_path, title=title, caption=caption, *args, **kwargs)


def add_callout_column(
    slide,
    callouts: List[Tuple[str, str]],
    x: Union[int, float, Length] = 8.5,
    y: Union[int, float, Length] = 1.9,
    w: Union[int, float, Length] = 4.0,
    h: Union[int, float, Length] = 5.0,
    accent_color: Optional[RGBColor] = None,
    *args,
    **kwargs
):
    """
    Renders an evenly-spaced vertical column of pedagogical callout cards
    explaining an adjacent hero graphic.
    Each item in callouts is a (title: str, text: str) tuple.
    """
    if not callouts:
        return []
    n = len(callouts)
    acc = accent_color or Theme.ACCENT_CYAN
    gap = 0.2
    total_gap = gap * (n - 1)
    card_h = max(1.0, (float(h) - total_gap) / n)

    cards = []
    current_y = float(y)
    for title, text in callouts:
        c = add_card(slide, x, current_y, w, card_h, title=title, body=text, accent_color=acc, title_size=11, body_size=10)
        cards.append(c)
        current_y += card_h + gap
    return cards


def add_step_flow(
    slide,
    x: Union[int, float, Length],
    y: Union[int, float, Length],
    w: Union[int, float, Length],
    h: Union[int, float, Length],
    steps: Optional[List[str]] = None,
    *args,
    **kwargs
):
    """Renders a connected sequence of pipeline stages."""
    stps = steps or kwargs.get("pipeline_steps") or kwargs.get("items") or []
    n = len(stps)
    if n == 0:
        return

    lx, ly, lw, lh = _to_length(x), _to_length(y), _to_length(w), _to_length(h)
    gap = _to_length(0.2)
    step_w = (lw - (gap * (n - 1))) / n

    for i, step_text in enumerate(stps):
        sx = lx + (i * (step_w + gap))
        add_card(
            slide,
            x=sx, y=ly, w=step_w, h=lh,
            title=f"STAGE {i+1}",
            body=str(step_text),
            accent_color=Theme.ACCENT_CYAN,
            title_size=10,
            body_size=11
        )


def add_badge_row(
    slide,
    x: Union[int, float, Length],
    y: Union[int, float, Length],
    badges: Optional[List[Tuple[str, str]]] = None,
    item_w: Union[int, float, Length] = 2.75,
    gap: Union[int, float, Length] = 0.24,
    h: Union[int, float, Length] = 0.9,
    *args,
    **kwargs
):
    """Renders an evenly spaced horizontal row of metadata chips."""
    bdgs = badges or kwargs.get("items") or kwargs.get("chips") or []
    lx, ly = _to_length(x), _to_length(y)
    liw, lgap, lh = _to_length(item_w), _to_length(gap), _to_length(h)

    for i, (b_title, b_val) in enumerate(bdgs):
        bx = lx + (i * (liw + lgap))
        add_metric_card(
            slide,
            x=bx, y=ly, w=liw, h=lh,
            label=str(b_title),
            value=str(b_val),
            accent_color=Theme.ACCENT_CYAN
        )

