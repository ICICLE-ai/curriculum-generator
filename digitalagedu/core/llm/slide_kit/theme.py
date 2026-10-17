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

