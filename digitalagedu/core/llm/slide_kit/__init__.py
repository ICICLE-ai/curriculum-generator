"""
slide_kit: Modern 16:9 Presentation Design & Layout System for PowerPoint.
Modularized into:
- theme: Theme colors, dimensions, and coordinate conversion/clamping
- layout: Base slide creation, headers, hero graphics, and callout columns
- cards: Container cards, metric KPI chips, and contrastive case studies
- media: Videos, images, and artifact comparisons
- code_blocks: Syntax-styled IDE code blocks and tables
"""

from digitalagedu.core.llm.slide_kit.theme import (
    Theme,
    _ThemeMeta,
    SLIDE_WIDTH_INCHES,
    SLIDE_HEIGHT_INCHES,
    _to_length,
    _clamp_bounds,
)

from digitalagedu.core.llm.slide_kit.layout import (
    create_slide,
    add_header,
    add_hero_graphic,
    add_callout_column,
    add_step_flow,
    add_badge_row,
)

from digitalagedu.core.llm.slide_kit.cards import (
    add_card,
    add_metric_card,
    add_contrastive_cards,
    add_callout_banner,
    add_text_box,
    add_text,
)

from digitalagedu.core.llm.slide_kit.media import (
    add_video,
    add_image,
    add_artifact_comparison,
)

from digitalagedu.core.llm.slide_kit.code_blocks import (
    add_code_box,
    add_table,
)

__all__ = [
    "Theme",
    "_ThemeMeta",
    "SLIDE_WIDTH_INCHES",
    "SLIDE_HEIGHT_INCHES",
    "_to_length",
    "_clamp_bounds",
    "create_slide",
    "add_header",
    "add_hero_graphic",
    "add_callout_column",
    "add_step_flow",
    "add_badge_row",
    "add_card",
    "add_metric_card",
    "add_contrastive_cards",
    "add_callout_banner",
    "add_text_box",
    "add_text",
    "add_video",
    "add_image",
    "add_artifact_comparison",
    "add_code_box",
    "add_table",
]

