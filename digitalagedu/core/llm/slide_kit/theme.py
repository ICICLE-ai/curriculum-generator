import os
from typing import Union, Tuple
from pptx.util import Inches, Length
from pptx.dml.color import RGBColor

# Standard 16:9 Widescreen dimensions
SLIDE_WIDTH_INCHES = 13.333
SLIDE_HEIGHT_INCHES = 7.5


def _to_length(val: Union[int, float, Length]) -> Length:
    """
    Safely converts a coordinate or dimension value to a pptx Length.
    - If already a Length object or a large integer (> 1000, i.e. already in EMUs), returns as-is.
    - If a float or small integer (<= 1000), treats it as inches and wraps with Inches(val).
    - Prevents double Inches(Inches(x)) multiplication that causes trillion-EMU coordinate overflows in PowerPoint.
    """
    if isinstance(val, Length):
        return val
    if isinstance(val, (int, float)):
        if val > 1000:
            return Length(int(val))
        return Inches(float(val))
    try:
        f_val = float(val)
        if f_val > 1000:
            return Length(int(f_val))
        return Inches(f_val)
    except (ValueError, TypeError):
        return Inches(1.0)


def _clamp_bounds(
    x: Union[int, float, Length],
    y: Union[int, float, Length],
    w: Union[int, float, Length],
    h: Union[int, float, Length],
    max_w: float = SLIDE_WIDTH_INCHES - 0.5,
    max_h: float = SLIDE_HEIGHT_INCHES - 0.4
) -> Tuple[Length, Length, Length, Length]:
    """
    Ensures any placed shape strictly fits within the 16:9 canvas dimensions.
    Prevents elements from rendering off the bottom or right of the slide.
    """
    def _as_inches(v):
        if isinstance(v, Length):
            return v.inches
        if isinstance(v, (int, float)):
            return v / 914400.0 if v > 1000 else float(v)
        try:
            fv = float(v)
            return fv / 914400.0 if fv > 1000 else fv
        except:
            return 1.0

    fx, fy, fw, fh = _as_inches(x), _as_inches(y), _as_inches(w), _as_inches(h)
    fx = max(0.4, min(fx, max_w - 1.0))
    fy = max(0.4, min(fy, max_h - 0.5))

    # Clamp width and height so x + w <= max_w and y + h <= max_h
    if fx + fw > max_w:
        fw = max(1.0, max_w - fx)
    if fy + fh > max_h:
        fh = max(0.5, max_h - fy)

    return _to_length(fx), _to_length(fy), _to_length(fw), _to_length(fh)


def _wrapped_line_count(line: str, chars_per_line: int) -> int:
    """Greedy word-wrap line count for one hard line of text."""
    lines, used = 1, 0
    for word in line.split():
        if used and used + 1 + len(word) > chars_per_line:
            lines, used = lines + 1, 0
        used += len(word) + (1 if used else 0)
        if used > chars_per_line:  # a word longer than the line breaks mid-word
            lines += (used - 1) // chars_per_line
            used = (used - 1) % chars_per_line + 1
    return lines


def _text_height_pt(paragraphs, sizes, width_in: float) -> float:
    total = 0.0
    for p, size in zip(paragraphs, sizes):
        em = 0.6 if p.font.name == "Consolas" else (0.56 if p.font.bold else 0.52)  # avg glyph width / font size
        cpl = max(1, int(width_in * 72 / (size * em)))
        n = sum(_wrapped_line_count(l, cpl) for l in p.text.replace("\v", "\n").split("\n"))
        total += n * size * 1.2 + (p.space_before.pt if p.space_before is not None else 0)
    return total


GROWN_TEXT = "Grown text"  # name of a text box _fit_text made taller; layout_issues tells the model to keep its size


def _font_pt(p) -> float:
    size = p.font.size or (p.runs[0].font.size if p.runs else None)
    return size.pt if size else 18.0


def _fit_text(tbox, min_pt: float = 8.0, min_scale: float = 0.75) -> int:
    """Keeps a text box's text inside the box: shrinks its fonts (to at most min_scale, never below min_pt) until the
    estimated wrapped height fits, then grows the box to the text's height. Text is never cut: '…' endings hid ~43
    lines a run (ee09eaac). Returns the EMUs the box grew, for callers to grow the card drawn behind it; the grown
    box may now overlap its neighbours, which layout_issues reports so the slide is laid out again.
    shortcut: height is estimated from average glyph widths (python-pptx cannot measure rendered text);
    TEXT_TO_FIT_SHAPE lets renderers that support shrink-on-overflow absorb the remaining estimate error."""
    from pptx.enum.text import MSO_AUTO_SIZE
    from pptx.util import Pt

    tf = tbox.text_frame
    tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    paras = list(tf.paragraphs)
    width_in = tbox.width / 914400 - 0.2           # default 0.1" left/right insets
    height_pt = (tbox.height / 914400 - 0.1) * 72  # default 0.05" top/bottom insets
    base = [_font_pt(p) for p in paras]

    scale, sizes = 1.0, base
    while _text_height_pt(paras, sizes, width_in) > height_pt and scale > min_scale + 1e-9:
        scale -= 0.05
        sizes = [max(min(b, min_pt), b * scale) for b in base]
    for p, s in zip(paras, sizes):
        p.font.size = Pt(round(s * 2) / 2)
    sizes = [p.font.size.pt for p in paras]

    needed_pt = _text_height_pt(paras, sizes, width_in)
    if needed_pt <= height_pt:
        return 0
    growth = int((needed_pt - height_pt) / 72 * 914400) + 2  # rounded up past float error, so the box holds its text
    tbox.height += growth
    tbox.name = GROWN_TEXT
    return growth


def layout_issues(slide, min_overlap_in: float = 0.05) -> list:
    """Fixes for elements that partly overlap or leave the slide, found from shape geometry alone (works when no
    screenshot can be rendered). A shape fully inside another (a card's text, an image in its frame) is intended,
    unless it sits on the text of a text box."""
    E = 914400
    shapes = list(slide.shapes)[1:]  # [0] is create_slide's full-slide background
    boxes = [(s.left / E, s.top / E, (s.left + s.width) / E, (s.top + s.height) / E) for s in shapes]

    def inside(a, b, tol=0.06):
        return a[0] >= b[0] - tol and a[1] >= b[1] - tol and a[2] <= b[2] + tol and a[3] <= b[3] + tol

    def name(i):
        # A card has no text itself; name it by the text box it contains
        group = [i] + [j for j in range(len(shapes)) if j != i and inside(boxes[j], boxes[i])]
        texts = [shapes[j].text_frame.text for j in group if shapes[j].has_text_frame and shapes[j].text_frame.text.strip()]
        what = f"'{texts[0].strip().splitlines()[0][:40]}'" if texts else ("the image" if shapes[i].shape_type == 13 else "a card")
        x0, y0, x1, y1 = boxes[i]
        grown = any(shapes[j].name == GROWN_TEXT for j in group)
        return f"{what} (x {x0:.2f}-{x1:.2f}, y {y0:.2f}-{y1:.2f} in{'; grown to fit its text, do not shrink it' if grown else ''})"

    issues = []
    # Week 2 of run ee09eaac put images and captions inside the explanation's text box, on top of its text
    for j, outer in enumerate(shapes):
        if outer.shape_type != 17 or not outer.text_frame.text.strip():
            continue
        paras = list(outer.text_frame.paragraphs)
        text_bottom = boxes[j][1] + 0.05 + _text_height_pt(paras, [_font_pt(p) for p in paras], boxes[j][2] - boxes[j][0] - 0.2) / 72
        for i in range(len(shapes)):
            if i != j and inside(boxes[i], boxes[j]) and not inside(boxes[j], boxes[i]) and boxes[i][1] < text_bottom - min_overlap_in:
                issues.append(f"{name(i)} sits on the text of {name(j)}; move it outside that text box.")

    # Compare top-level elements only, so a card and its own text box report one collision, not four
    # (of two identical boxes, the later one counts as nested)
    top = [i for i in range(len(boxes)) if not any(
        k != i and inside(boxes[i], boxes[k]) and (not inside(boxes[k], boxes[i]) or k < i) for k in range(len(boxes)))]
    for n, i in enumerate(top):
        a = boxes[i]
        if a[0] < -0.01 or a[1] < -0.01 or a[2] > SLIDE_WIDTH_INCHES + 0.01 or a[3] > SLIDE_HEIGHT_INCHES + 0.01:
            issues.append(f"{name(i)} runs off the {SLIDE_WIDTH_INCHES} x {SLIDE_HEIGHT_INCHES} in slide; move or shrink it.")
        for j in top[n + 1:]:
            b = boxes[j]
            w, h = min(a[2], b[2]) - max(a[0], b[0]), min(a[3], b[3]) - max(a[1], b[1])
            if w > min_overlap_in and h > min_overlap_in:
                issues.append(f"{name(i)} overlaps {name(j)} by {w:.2f} x {h:.2f} in; move one so they do not touch.")
    return issues


class _ThemeMeta(type):
    """Metaclass providing graceful typo tolerance for Theme attribute access."""
    def __getattr__(cls, name: str) -> RGBColor:
        clean = name.upper().replace("_", "")
        # Try direct or substring match against known colors
        for key, val in cls.__dict__.items():
            if isinstance(val, RGBColor) and key.startswith("ACCENT_"):
                if key.replace("ACCENT_", "").replace("_", "") in clean or clean in key.replace("_", ""):
                    return val
        if "BG" in clean:
            return cls.BG_DARK
        if "TEXT" in clean or "WHITE" in clean:
            return cls.TEXT_PRIMARY
        if "MUTED" in clean or "GRAY" in clean or "GREY" in clean:
            return cls.TEXT_MUTED
        if "CODE" in clean:
            return cls.CODE_BG
        # Default safe high-visibility cyan accent
        return cls.ACCENT_CYAN


class Theme(metaclass=_ThemeMeta):
    """Pre-calibrated 16:9 modern presentation color palette with typo-tolerant attribute access."""
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

