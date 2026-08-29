import os
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

logger = logging.getLogger(__name__)

# Standard 16:9 Widescreen dimensions
SLIDE_WIDTH_INCHES = 13.333
SLIDE_HEIGHT_INCHES = 7.5


class Theme:
    """Pre-calibrated 16:9 modern presentation color palette."""
    BG_DARK = RGBColor(11, 15, 25)           # #0B0F19 Deep slate midnight
    BG_LIGHT = RGBColor(248, 250, 252)       # #F8FAFC Clean studio light
    CARD_BG = RGBColor(30, 41, 59)          # #1E293B Card container background
    CARD_BORDER = RGBColor(51, 65, 85)       # #334155 Card border stroke
    TEXT_PRIMARY = RGBColor(248, 250, 252)   # #F8FAFC High-contrast white
    TEXT_MUTED = RGBColor(148, 163, 184)     # #94A3B8 Secondary cool gray
    ACCENT_CYAN = RGBColor(56, 189, 248)     # #38BDF8 Electric Cyan
    ACCENT_INDIGO = RGBColor(99, 102, 241)   # #6366F1 Modern Indigo
    ACCENT_EMERALD = RGBColor(16, 185, 129)  # #10B981 Success Emerald
    ACCENT_CORAL = RGBColor(239, 68, 68)     # #EF4444 Diagnostic Coral / Alert
    ACCENT_GOLD = RGBColor(245, 158, 11)     # #F59E0B Highlight Amber
    CODE_BG = RGBColor(15, 23, 42)           # #0F172A Dark IDE Canvas
    CODE_TEXT = RGBColor(226, 232, 240)      # #E2E8F0 Monospaced code text


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
        Inches(0.8), Inches(0.5), Inches(pill_w), Inches(0.38)
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
    tbox = slide.shapes.add_textbox(Inches(0.8), Inches(0.95), Inches(11.733), Inches(0.9))
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


def add_card(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    title: Optional[str] = None,
    body: Optional[str] = None,
    bg_color: Optional[RGBColor] = None,
    border_color: Optional[RGBColor] = None,
    accent_color: Optional[RGBColor] = None,
    title_size: int = 12,
    body_size: int = 12,
    *args,
    **kwargs
):
    """Adds a rounded rectangular card container with optional title and body paragraphs."""
    t = title or kwargs.get("heading") or kwargs.get("header")
    b = body or kwargs.get("text") or kwargs.get("content") or kwargs.get("description")
    bg = bg_color or kwargs.get("bg") or Theme.CARD_BG
    border = border_color or kwargs.get("border") or Theme.CARD_BORDER
    acc = accent_color or kwargs.get("accent") or Theme.ACCENT_CYAN

    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h)
    )
    card.fill.solid()
    card.fill.fore_color.rgb = bg
    card.line.color.rgb = border
    card.line.width = Pt(1.5)

    if t or b:
        pad_x = 0.2
        pad_y = 0.18
        tbox = slide.shapes.add_textbox(
            Inches(x + pad_x), Inches(y + pad_y),
            Inches(w - (2 * pad_x)), Inches(h - (2 * pad_y))
        )
        tf = tbox.text_frame
        tf.word_wrap = True

        first = True
        if t:
            p_t = tf.paragraphs[0]
            p_t.text = str(t)
            p_t.font.size = Pt(title_size)
            p_t.font.bold = True
            p_t.font.color.rgb = acc
            first = False

        if b:
            p_b = tf.paragraphs[0] if first else tf.add_paragraph()
            p_b.text = str(b)
            p_b.font.size = Pt(body_size)
            p_b.font.color.rgb = Theme.TEXT_PRIMARY
            if not first:
                p_b.space_before = Pt(6)

    return card


def add_code_box(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    code: Optional[str] = None,
    title: Optional[str] = None,
    font_size: float = 9.5,
    *args,
    **kwargs
):
    """Renders a syntax-styled dark IDE code block with monospaced font."""
    raw_code = code or kwargs.get("code_string") or kwargs.get("code_str") or kwargs.get("text") or ""
    t = title or kwargs.get("heading") or kwargs.get("header")

    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h)
    )
    card.fill.solid()
    card.fill.fore_color.rgb = Theme.CODE_BG
    card.line.color.rgb = Theme.CARD_BORDER
    card.line.width = Pt(1.5)

    tbox = slide.shapes.add_textbox(
        Inches(x + 0.2), Inches(y + 0.15),
        Inches(w - 0.4), Inches(h - 0.3)
    )
    tf = tbox.text_frame
    tf.word_wrap = True

    first = True
    if t:
        p_t = tf.paragraphs[0]
        p_t.text = str(t).upper()
        p_t.font.size = Pt(10)
        p_t.font.bold = True
        p_t.font.color.rgb = Theme.ACCENT_CYAN
        first = False

    lines = [l for l in str(raw_code).strip().split("\n") if not l.startswith('"""') and not l.startswith("'''")]
    display_code = "\n".join(lines[:24]) if lines else str(raw_code)

    p_c = tf.paragraphs[0] if first else tf.add_paragraph()
    p_c.text = display_code
    p_c.font.name = "Consolas"
    p_c.font.size = Pt(font_size)
    p_c.font.color.rgb = Theme.CODE_TEXT
    if not first:
        p_c.space_before = Pt(4)

    return card


def add_metric_card(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    label: Optional[str] = None,
    value: Optional[Any] = None,
    subtext: Optional[str] = None,
    accent_color: Optional[RGBColor] = None,
    *args,
    **kwargs
):
    """Renders a high-impact KPI statistic card."""
    lbl = label or kwargs.get("title") or kwargs.get("name") or ""
    val = value if value is not None else (kwargs.get("val") or kwargs.get("metric") or "")
    sub = subtext or kwargs.get("subtitle") or kwargs.get("sub") or kwargs.get("description")
    acc = accent_color or kwargs.get("accent") or Theme.ACCENT_CYAN

    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h)
    )
    card.fill.solid()
    card.fill.fore_color.rgb = Theme.CARD_BG
    card.line.color.rgb = Theme.CARD_BORDER
    card.line.width = Pt(1.5)

    tbox = slide.shapes.add_textbox(
        Inches(x + 0.15), Inches(y + 0.12),
        Inches(w - 0.3), Inches(h - 0.24)
    )
    tf = tbox.text_frame
    tf.word_wrap = True

    # Label
    p_lbl = tf.paragraphs[0]
    p_lbl.text = str(lbl).upper()
    p_lbl.font.size = Pt(9)
    p_lbl.font.bold = True
    p_lbl.font.color.rgb = Theme.TEXT_MUTED

    # Value
    p_val = tf.add_paragraph()
    p_val.text = str(val)
    p_val.font.size = Pt(20)
    p_val.font.bold = True
    p_val.font.color.rgb = acc
    p_val.space_before = Pt(2)

    # Subtext
    if sub:
        p_sub = tf.add_paragraph()
        p_sub.text = str(sub)
        p_sub.font.size = Pt(9.5)
        p_sub.font.color.rgb = Theme.TEXT_MUTED
        p_sub.space_before = Pt(2)

    return card


def add_badge_row(
    slide,
    x: float,
    y: float,
    badges: Optional[List[Tuple[str, str]]] = None,
    item_w: float = 2.75,
    gap: float = 0.24,
    h: float = 0.9,
    *args,
    **kwargs
):
    """Renders an evenly spaced horizontal row of metadata chips."""
    bdgs = badges or kwargs.get("items") or kwargs.get("chips") or []
    for i, (b_title, b_val) in enumerate(bdgs):
        bx = x + i * (item_w + gap)
        add_metric_card(
            slide,
            x=bx, y=y, w=item_w, h=h,
            label=str(b_title),
            value=str(b_val),
            accent_color=Theme.ACCENT_CYAN
        )


def add_contrastive_cards(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    success_data: Optional[Dict[str, Any]] = None,
    failure_data: Optional[Dict[str, Any]] = None,
    *args,
    **kwargs
):
    """
    Renders side-by-side diagnostic case studies (Top Success vs Hard Failure).
    Accepts any keyword alias (success_data, success_dict, success, top_success, failure_data, failure_dict, failure, hard_failure).
    """
    succ = (
        success_data or 
        kwargs.get("success_dict") or 
        kwargs.get("success") or 
        kwargs.get("top_success") or 
        (args[0] if len(args) > 0 else {}) or 
        {}
    )
    fail = (
        failure_data or 
        kwargs.get("failure_dict") or 
        kwargs.get("failure") or 
        kwargs.get("hard_failure") or 
        (args[1] if len(args) > 1 else {}) or 
        {}
    )

    col_w = (w - 0.3) / 2.0

    # 1. Success Card (Emerald)
    add_card(
        slide,
        x=x, y=y, w=col_w, h=h,
        title="HIGH-CONFIDENCE MATCH (SUCCESS)",
        body=(
            f"Sample: {os.path.basename(succ.get('image_path', 'sample.jpg')) if isinstance(succ, dict) else 'sample.jpg'}\n"
            f"Ground Truth: {succ.get('ground_truth', 'Target') if isinstance(succ, dict) else 'Target'}\n"
            f"Prediction: {succ.get('predicted_class', succ.get('ground_truth', 'Target')) if isinstance(succ, dict) else 'Target'}\n"
            f"Probabilities: {succ.get('probabilities', 'High Confidence') if isinstance(succ, dict) else 'High Confidence'}"
        ),
        accent_color=Theme.ACCENT_EMERALD,
        title_size=11,
        body_size=11
    )

    # 2. Failure Card (Coral Red)
    add_card(
        slide,
        x=x + col_w + 0.3, y=y, w=col_w, h=h,
        title="DIAGNOSTIC FAILURE MODE (EDGE CASE)",
        body=(
            f"Sample: {os.path.basename(fail.get('image_path', 'failure.jpg')) if isinstance(fail, dict) else 'failure.jpg'}\n"
            f"Ground Truth: {fail.get('ground_truth', 'True Class') if isinstance(fail, dict) else 'True Class'}\n"
            f"Predicted: {fail.get('predicted_class', 'Misclassified') if isinstance(fail, dict) else 'Misclassified'}\n"
            f"Probabilities: {fail.get('probabilities', 'Shifted Decision Boundary') if isinstance(fail, dict) else 'Shifted Boundary'}"
        ),
        accent_color=Theme.ACCENT_CORAL,
        title_size=11,
        body_size=11
    )


def add_step_flow(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    steps: Optional[List[str]] = None,
    *args,
    **kwargs
):
    """Renders a connected sequence of pipeline stages."""
    stps = steps or kwargs.get("pipeline_steps") or kwargs.get("items") or []
    n = len(stps)
    if n == 0:
        return
    gap = 0.2
    step_w = (w - (n - 1) * gap) / n

    for i, step_text in enumerate(stps):
        sx = x + i * (step_w + gap)
        add_card(
            slide,
            x=sx, y=y, w=step_w, h=h,
            title=f"STAGE {i+1}",
            body=str(step_text),
            accent_color=Theme.ACCENT_CYAN,
            title_size=10,
            body_size=11
        )


def add_callout_banner(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    text: Optional[str] = None,
    title: str = "KEY PEDAGOGICAL TAKEAWAY",
    accent_color: Optional[RGBColor] = None,
    *args,
    **kwargs
):
    """Renders a full-width takeaway callout card with accent header."""
    txt = text or kwargs.get("body") or kwargs.get("content") or ""
    t = title or kwargs.get("heading") or "KEY PEDAGOGICAL TAKEAWAY"
    acc = accent_color or kwargs.get("accent") or Theme.ACCENT_GOLD
    return add_card(
        slide,
        x=x, y=y, w=w, h=h,
        title=str(t),
        body=str(txt),
        accent_color=acc,
        title_size=10,
        body_size=11.5
    )


def add_table(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    headers: Optional[List[str]] = None,
    rows: Optional[List[List[str]]] = None,
    *args,
    **kwargs
):
    """Renders a styled data comparison table on the slide."""
    hdrs = headers or kwargs.get("columns") or []
    rws = rows or kwargs.get("data") or []
    num_rows = len(rws) + 1
    num_cols = len(hdrs)
    table_shape = slide.shapes.add_table(
        num_rows, num_cols, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    table = table_shape.table

    for c_idx, head in enumerate(hdrs):
        cell = table.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = Theme.CARD_BG
        p = cell.text_frame.paragraphs[0]
        p.text = str(head).upper()
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = Theme.ACCENT_CYAN
        p.alignment = PP_ALIGN.CENTER

    for r_idx, row in enumerate(rws):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx + 1, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = Theme.CODE_BG
            p = cell.text_frame.paragraphs[0]
            p.text = str(val)
            p.font.size = Pt(10)
            p.font.color.rgb = Theme.TEXT_PRIMARY
            p.alignment = PP_ALIGN.CENTER

    return table_shape
