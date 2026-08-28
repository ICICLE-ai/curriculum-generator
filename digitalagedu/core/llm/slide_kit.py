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


def create_slide(prs: Presentation, bg_color: Optional[RGBColor] = None):
    """Creates a new blank 16:9 slide with a full-bleed solid background."""
    prs.slide_width = Inches(SLIDE_WIDTH_INCHES)
    prs.slide_height = Inches(SLIDE_HEIGHT_INCHES)
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    bg = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        0, 0, Inches(SLIDE_WIDTH_INCHES), Inches(SLIDE_HEIGHT_INCHES)
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = bg_color or Theme.BG_DARK
    bg.line.fill.background()
    return slide


def add_header(
    slide,
    tag: str,
    title: str,
    subtitle: Optional[str] = None,
    tag_color: Optional[RGBColor] = None
):
    """Adds a standardized top category pill, bold title, and optional subtitle."""
    accent = tag_color or Theme.ACCENT_CYAN
    
    # 1. Category pill
    pill_w = max(2.2, len(tag) * 0.11 + 0.5)
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
    p_pill.text = tag.upper()
    p_pill.font.size = Pt(9.5)
    p_pill.font.bold = True
    p_pill.font.color.rgb = accent
    p_pill.alignment = PP_ALIGN.CENTER

    # 2. Main title & subtitle
    tbox = slide.shapes.add_textbox(Inches(0.8), Inches(0.95), Inches(11.733), Inches(0.9))
    tf = tbox.text_frame
    tf.word_wrap = True
    p_title = tf.paragraphs[0]
    p_title.text = title
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = Theme.TEXT_PRIMARY

    if subtitle:
        p_sub = tf.add_paragraph()
        p_sub.text = subtitle
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
    body_size: int = 12
):
    """Adds a rounded rectangular card container with optional title and body paragraphs."""
    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h)
    )
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color or Theme.CARD_BG
    card.line.color.rgb = border_color or Theme.CARD_BORDER
    card.line.width = Pt(1.5)

    if title or body:
        pad_x = 0.2
        pad_y = 0.18
        tbox = slide.shapes.add_textbox(
            Inches(x + pad_x), Inches(y + pad_y),
            Inches(w - (2 * pad_x)), Inches(h - (2 * pad_y))
        )
        tf = tbox.text_frame
        tf.word_wrap = True

        first = True
        if title:
            p_t = tf.paragraphs[0]
            p_t.text = title
            p_t.font.size = Pt(title_size)
            p_t.font.bold = True
            p_t.font.color.rgb = accent_color or Theme.ACCENT_CYAN
            first = False

        if body:
            p_b = tf.paragraphs[0] if first else tf.add_paragraph()
            p_b.text = body
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
    code: str,
    title: Optional[str] = None,
    font_size: float = 9.5
):
    """Renders a syntax-styled dark IDE code block with monospaced font."""
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
    if title:
        p_t = tf.paragraphs[0]
        p_t.text = title.upper()
        p_t.font.size = Pt(10)
        p_t.font.bold = True
        p_t.font.color.rgb = Theme.ACCENT_CYAN
        first = False

    lines = [l for l in code.strip().split("\n") if not l.startswith('"""') and not l.startswith("'''")]
    display_code = "\n".join(lines[:24]) if lines else code

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
    label: str,
    value: str,
    subtext: Optional[str] = None,
    accent_color: Optional[RGBColor] = None
):
    """Renders a high-impact KPI statistic card."""
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
    p_lbl.text = label.upper()
    p_lbl.font.size = Pt(9)
    p_lbl.font.bold = True
    p_lbl.font.color.rgb = Theme.TEXT_MUTED

    # Value
    p_val = tf.add_paragraph()
    p_val.text = str(value)
    p_val.font.size = Pt(20)
    p_val.font.bold = True
    p_val.font.color.rgb = accent_color or Theme.ACCENT_CYAN
    p_val.space_before = Pt(2)

    # Subtext
    if subtext:
        p_sub = tf.add_paragraph()
        p_sub.text = subtext
        p_sub.font.size = Pt(9.5)
        p_sub.font.color.rgb = Theme.TEXT_MUTED
        p_sub.space_before = Pt(2)

    return card


def add_badge_row(
    slide,
    x: float,
    y: float,
    badges: List[Tuple[str, str]],
    item_w: float = 2.75,
    gap: float = 0.24,
    h: float = 0.9
):
    """Renders an evenly spaced horizontal row of metadata chips."""
    for i, (b_title, b_val) in enumerate(badges):
        bx = x + i * (item_w + gap)
        add_metric_card(
            slide,
            x=bx, y=y, w=item_w, h=h,
            label=b_title,
            value=b_val,
            accent_color=Theme.ACCENT_CYAN
        )


def add_contrastive_cards(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    success_data: Dict[str, Any],
    failure_data: Dict[str, Any]
):
    """Renders side-by-side diagnostic case studies (Top Success vs Hard Failure)."""
    col_w = (w - 0.3) / 2.0

    # 1. Success Card (Emerald)
    add_card(
        slide,
        x=x, y=y, w=col_w, h=h,
        title="HIGH-CONFIDENCE MATCH (SUCCESS)",
        body=(
            f"Sample: {os.path.basename(success_data.get('image_path', 'sample.jpg'))}\n"
            f"Ground Truth: {success_data.get('ground_truth', 'Target')}\n"
            f"Prediction: {success_data.get('predicted_class', success_data.get('ground_truth', 'Target'))}\n"
            f"Probabilities: {success_data.get('probabilities', 'High Confidence')}"
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
            f"Sample: {os.path.basename(failure_data.get('image_path', 'failure.jpg'))}\n"
            f"Ground Truth: {failure_data.get('ground_truth', 'True Class')}\n"
            f"Predicted: {failure_data.get('predicted_class', 'Misclassified')}\n"
            f"Probabilities: {failure_data.get('probabilities', 'Shifted Decision Boundary')}"
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
    steps: List[str]
):
    """Renders a connected sequence of pipeline stages."""
    n = len(steps)
    if n == 0:
        return
    gap = 0.2
    step_w = (w - (n - 1) * gap) / n

    for i, step_text in enumerate(steps):
        sx = x + i * (step_w + gap)
        add_card(
            slide,
            x=sx, y=y, w=step_w, h=h,
            title=f"STAGE {i+1}",
            body=step_text,
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
    text: str,
    title: str = "KEY PEDAGOGICAL TAKEAWAY",
    accent_color: Optional[RGBColor] = None
):
    """Renders a full-width takeaway callout card with accent header."""
    return add_card(
        slide,
        x=x, y=y, w=w, h=h,
        title=title,
        body=text,
        accent_color=accent_color or Theme.ACCENT_GOLD,
        title_size=10,
        body_size=11.5
    )


def add_table(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    headers: List[str],
    rows: List[List[str]]
):
    """Renders a styled data comparison table on the slide."""
    num_rows = len(rows) + 1
    num_cols = len(headers)
    table_shape = slide.shapes.add_table(
        num_rows, num_cols, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    table = table_shape.table

    for c_idx, head in enumerate(headers):
        cell = table.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = Theme.CARD_BG
        p = cell.text_frame.paragraphs[0]
        p.text = head.upper()
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = Theme.ACCENT_CYAN
        p.alignment = PP_ALIGN.CENTER

    for r_idx, row in enumerate(rows):
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
