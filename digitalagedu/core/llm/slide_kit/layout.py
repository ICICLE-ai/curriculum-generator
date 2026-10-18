from typing import List, Optional, Tuple, Union, Dict, Any
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


def add_split_slide(
    prs: Presentation,
    title: str,
    subtitle: Optional[str] = None,
    left_content: Optional[Union[List[str], List[Tuple[str, str]], str]] = None,
    image_path: Optional[str] = None,
    category: str = "CURRICULUM",
    *args,
    **kwargs
):
    """
    Creates a new 16:9 slide with header, hero graphic, and pedagogical callout column.
    """
    slide = create_slide(prs)
    add_header(slide, tag=category, title=title, subtitle=subtitle)

    img = image_path or kwargs.get("graphic_path") or kwargs.get("path")
    if img:
        add_hero_graphic(slide, img, x=0.8, y=1.9, w=7.2, h=5.0)

    # Format callouts / notes
    content = left_content or kwargs.get("bullets") or kwargs.get("notes") or []
    callouts = []
    if isinstance(content, list):
        for i, item in enumerate(content):
            if isinstance(item, tuple) and len(item) >= 2:
                callouts.append((str(item[0]), str(item[1])))
            elif isinstance(item, dict):
                callouts.append((str(item.get("title", f"Point {i+1}")), str(item.get("body", item.get("desc", "")))))
            else:
                callouts.append((f"Key Point {i+1}", str(item)))
    elif isinstance(content, str):
        callouts.append(("Key Takeaway", content))

    if img:
        if callouts:
            add_callout_column(slide, callouts[:4], x=8.3, y=1.9, w=4.2, h=5.0)
    else:
        if callouts:
            mid = max(1, (len(callouts) + 1) // 2)
            left_col = callouts[:mid]
            right_col = callouts[mid:]
            add_callout_column(slide, left_col, x=0.8, y=1.9, w=5.6, h=5.0)
            if right_col:
                add_callout_column(slide, right_col, x=6.8, y=1.9, w=5.7, h=5.0)

    return slide


def add_card_slide(
    prs: Presentation,
    title: str,
    subtitle: Optional[str] = None,
    cards: Optional[List[Union[Dict[str, Any], Tuple[str, str], str]]] = None,
    category: str = "CURRICULUM",
    *args,
    **kwargs
):
    """
    Creates a new 16:9 slide with header and multiple side-by-side thematic cards.
    """
    slide = create_slide(prs)
    add_header(slide, tag=category, title=title, subtitle=subtitle)

    raw_cards = cards or kwargs.get("columns") or kwargs.get("items") or []
    if not raw_cards:
        raw_cards = [{"title": "Overview", "body": subtitle or title}]

    n = min(len(raw_cards), 4)
    gap = 0.25
    usable_w = 11.733 - (gap * (n - 1))
    card_w = max(2.5, usable_w / n)
    start_x = 0.8

    for i in range(n):
        item = raw_cards[i]
        c_x = start_x + i * (card_w + gap)
        if isinstance(item, dict):
            c_title = item.get("title", f"Subsystem {i+1}")
            bullets = item.get("bullets", [])
            body_text = "\n".join(f"• {b}" for b in bullets) if bullets else item.get("body", item.get("desc", ""))
        elif isinstance(item, tuple) and len(item) >= 2:
            c_title = str(item[0])
            body_text = str(item[1])
        else:
            c_title = f"Component {i+1}"
            body_text = str(item)

        add_card(slide, x=c_x, y=1.9, w=card_w, h=5.0, title=c_title, body=body_text)

    return slide


def add_metric_slide(
    prs: Presentation,
    title: str,
    subtitle: Optional[str] = None,
    metrics: Optional[List[Dict[str, Any]]] = None,
    notes: Optional[Union[str, List[str]]] = None,
    category: str = "BENCHMARKS",
    *args,
    **kwargs
):
    """
    Creates a new 16:9 slide with header, top KPI metric chips, and explanatory analysis cards below.
    """
    slide = create_slide(prs)
    add_header(slide, tag=category, title=title, subtitle=subtitle)

    raw_metrics = metrics or [
        {"label": "ACCURACY", "value": "93.4%"},
        {"label": "AUC-ROC", "value": "0.981"},
        {"label": "CONVERGENCE", "value": "32 Ep."}
    ]
    m_count = min(len(raw_metrics), 4)
    m_gap = 0.25
    usable_w = 11.733 - (m_gap * (m_count - 1))
    item_w = max(2.5, usable_w / m_count)

    for i in range(m_count):
        m = raw_metrics[i]
        mx = 0.8 + i * (item_w + m_gap)
        lbl = m.get("label", m.get("name", "Metric"))
        val = str(m.get("value", m.get("score", "90%")))
        delta = m.get("delta")
        sub = m.get("subtext")
        add_metric_card(slide, x=mx, y=1.9, w=item_w, h=1.6, label=lbl, value=val, delta=delta, subtext=sub)

    # Notes section below
    raw_notes = notes or kwargs.get("bullets") or kwargs.get("findings")
    if raw_notes:
        body = "\n".join(f"• {b}" for b in raw_notes) if isinstance(raw_notes, list) else str(raw_notes)
        add_card(slide, x=0.8, y=3.8, w=11.733, h=3.1, title="Empirical Evaluation & Performance Analysis", body=body)

    return slide


def add_code_slide(
    prs: Presentation,
    title: str,
    subtitle: Optional[str] = None,
    code: str = "",
    notes: Optional[Union[str, List[str]]] = None,
    language: str = "python",
    category: str = "IMPLEMENTATION",
    *args,
    **kwargs
):
    """
    Creates a new 16:9 slide with header, syntax-styled IDE code box, and pedagogical margin notes.
    """
    from digitalagedu.core.llm.slide_kit.code_blocks import add_code_box
    slide = create_slide(prs)
    add_header(slide, tag=category, title=title, subtitle=subtitle)

    add_code_box(slide, x=0.8, y=1.9, w=7.4, h=5.0, code=code, title="Python Implementation")

    raw_notes = notes or kwargs.get("bullets") or kwargs.get("takeaways")
    body = "\n".join(f"• {b}" for b in raw_notes) if isinstance(raw_notes, list) else str(raw_notes or "Core architectural contracts and execution flow.")
    add_card(slide, x=8.5, y=1.9, w=4.0, h=5.0, title="Architectural Contracts", body=body)

    return slide


def add_title_slide(
    prs: Presentation,
    title: str,
    subtitle: Optional[str] = None,
    category: str = "CURRICULUM",
    *args,
    **kwargs
):
    """
    Creates an elegant, high-impact introductory title slide.
    """
    slide = create_slide(prs)
    add_header(slide, tag=category, title=title, subtitle=subtitle)
    add_card(
        slide,
        x=0.8, y=2.2, w=11.733, h=4.6,
        title="Module Learning Path",
        body=kwargs.get("description", "A hands-on computing curriculum module bridging domain concepts, deep learning architectures, and verified code implementations.")
    )
    return slide


