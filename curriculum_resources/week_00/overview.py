"""
WEEK 00
DigitalAgEdu — Pipeline Overview
See the full AI workflow before you build it.
"""

import os
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import textwrap

# ----------------------------
# Config — point at any image
# from your dataset to run live
# ----------------------------
DATASET_ROOT = "/fs/ess/PAS2699/AI_Presidency_Dataset_CSG/Corn/Corn"
OUTPUT_DIR = "./week00_overview_output"
SAMPLE_COUNT = 3


# ----------------------------
# Pipeline stage definitions
# ----------------------------
STAGES = [
    {
        "number": 1,
        "week": "Weeks 1–5",
        "name": "Data Collection & Exploration",
        "what": "Raw agricultural images organized into class folders.",
        "why": "Every AI system starts with data. You'll learn what makes a good dataset — class balance, image quality, diversity — and why these choices directly affect accuracy later.",
        "output": "A labeled folder of images ready for processing.",
    },
    {
        "number": 2,
        "week": "Week 6",
        "name": "Preprocessing & Augmentation",
        "what": "Images are resized, normalized, and randomly flipped/rotated.",
        "why": "Raw images come in different sizes and lighting conditions. Preprocessing makes them consistent. Augmentation artificially expands the dataset so the model generalizes better.",
        "output": "Uniform NumPy arrays ready for a neural network.",
    },
    {
        "number": 3,
        "week": "Weeks 7–8",
        "name": "Classification (DINOv2)",
        "what": "A pre-trained vision model is fine-tuned to identify corn diseases.",
        "why": "Training from scratch on small agricultural datasets fails. Transfer learning lets you borrow knowledge from a model trained on millions of images and adapt it to your specific task in minutes.",
        "output": "A prediction: e.g. 'Northern Corn Leaf Blight' with confidence score.",
    },
    {
        "number": 4,
        "week": "Week 9",
        "name": "Segmentation (SAM)",
        "what": "The Segment Anything Model isolates just the leaf region from each image.",
        "why": "Background soil, sky, and other crops introduce noise. Segmentation lets downstream analysis focus on the leaf itself, improving damage estimates.",
        "output": "A binary mask and a cropped leaf image with background removed.",
    },
    {
        "number": 5,
        "week": "Week 10",
        "name": "Damage Estimation (HSV)",
        "what": "The segmented leaf is analyzed in HSV color space to quantify diseased area.",
        "why": "Classification tells you *what* disease is present. Damage estimation tells you *how bad* it is — a number farmers can act on.",
        "output": "A damage percentage, e.g. '16.89%'.",
    },
]


# ----------------------------
# Helpers
# ----------------------------
def load_sample_images(dataset_root, n=SAMPLE_COUNT):
    valid_ext = (".jpg", ".jpeg", ".png")
    all_images = []
    for root, _, files in os.walk(dataset_root):
        for f in files:
            if f.lower().endswith(valid_ext):
                all_images.append(os.path.join(root, f))
    if not all_images:
        return []
    random.seed(0)
    return random.sample(all_images, min(n, len(all_images)))


def get_class_from_path(path):
    parts = path.split(os.sep)
    return parts[-2] if len(parts) >= 2 else "Unknown"


def make_thumbnail(image_path, size=(200, 200)):
    img = Image.open(image_path).convert("RGB")
    img.thumbnail(size)
    background = Image.new("RGB", size, (30, 30, 30))
    offset = ((size[0] - img.width) // 2, (size[1] - img.height) // 2)
    background.paste(img, offset)
    return background


def draw_wrapped_text(draw, text, x, y, max_width, font, fill, line_spacing=6):
    lines = textwrap.wrap(text, width=max_width)
    current_y = y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_height = bbox[3] - bbox[1]
        draw.text((x, current_y), line, font=font, fill=fill)
        current_y += line_height + line_spacing
    return current_y


def render_pipeline_card(stage, width=900):
    """Render a single pipeline stage as a PIL image card."""
    height = 240
    card = Image.new("RGB", (width, height), (18, 18, 24))
    draw = ImageDraw.Draw(card)

    # Left accent bar
    accent_color = (80, 200, 120)
    draw.rectangle([(0, 0), (6, height)], fill=accent_color)

    # Stage number circle
    cx, cy, r = 50, 60, 24
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=accent_color)

    try:
        num_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except Exception:
        num_font = title_font = body_font = small_font = ImageFont.load_default()

    # Stage number
    num_text = str(stage["number"])
    bbox = draw.textbbox((0, 0), num_text, font=num_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy - th // 2), num_text, font=num_font, fill=(10, 10, 10))

    # Week badge
    draw.rounded_rectangle([(20, 96), (90, 116)], radius=4, fill=(40, 40, 55))
    draw.text((25, 99), stage["week"], font=small_font, fill=(160, 160, 200))

    # Title
    draw.text((110, 18), stage["symbol"] + "  " + stage["name"], font=title_font, fill=(240, 240, 240))

    # What / Why / Output
    y = 50
    draw.text((110, y), "What:", font=body_font, fill=accent_color)
    y = draw_wrapped_text(draw, stage["what"], 160, y, 85, body_font, (200, 200, 200))

    y += 4
    draw.text((110, y), "Why:", font=body_font, fill=(255, 200, 80))
    y = draw_wrapped_text(draw, stage["why"], 160, y, 85, body_font, (200, 200, 200))

    y += 4
    draw.text((110, y), "Output:", font=body_font, fill=(100, 180, 255))
    draw_wrapped_text(draw, stage["output"], 180, y, 80, body_font, (200, 200, 200))

    return card


def render_sample_strip(image_paths):
    """Render a horizontal strip of sample images with class labels."""
    thumb_size = (200, 200)
    padding = 16
    label_height = 28
    strip_width = (thumb_size[0] + padding) * len(image_paths) + padding
    strip_height = thumb_size[1] + label_height + padding * 2

    strip = Image.new("RGB", (strip_width, strip_height), (12, 12, 18))
    draw = ImageDraw.Draw(strip)

    try:
        label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
    except Exception:
        label_font = ImageFont.load_default()

    for i, path in enumerate(image_paths):
        x = padding + i * (thumb_size[0] + padding)
        y = padding
        thumb = make_thumbnail(path, thumb_size)
        strip.paste(thumb, (x, y))
        label = get_class_from_path(path)
        label_short = label[:24] + "…" if len(label) > 24 else label
        draw.text((x + 4, y + thumb_size[1] + 4), label_short, font=label_font, fill=(180, 220, 160))

    return strip


def render_full_overview(image_paths, output_path):
    card_width = 900
    card_height = 240
    gap = 12
    header_height = 100
    sample_strip_height = 260
    footer_height = 60

    total_height = (
        header_height
        + sample_strip_height
        + gap
        + len(STAGES) * (card_height + gap)
        + footer_height
    )

    canvas = Image.new("RGB", (card_width, total_height), (10, 10, 16))
    draw = ImageDraw.Draw(canvas)

    try:
        h1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        h2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except Exception:
        h1 = h2 = footer_font = ImageFont.load_default()

    # Header
    draw.text((32, 20), "DigitalAgEdu — AI Pipeline Overview", font=h1, fill=(240, 240, 240))
    draw.text((32, 58), "From raw field images to disease detection and damage quantification.", font=h2, fill=(140, 160, 180))
    draw.line([(32, 88), (card_width - 32, 88)], fill=(50, 50, 70), width=1)

    # Sample strip
    if image_paths:
        strip = render_sample_strip(image_paths)
        strip_x = (card_width - strip.width) // 2
        canvas.paste(strip, (strip_x, header_height))

    y_offset = header_height + sample_strip_height + gap

    # Stage cards
    for stage in STAGES:
        card = render_pipeline_card(stage, width=card_width)
        canvas.paste(card, (0, y_offset))

        # Arrow connector (skip after last)
        if stage["number"] < len(STAGES):
            ax = card_width // 2
            ay = y_offset + card_height + 2
            draw.line([(ax, ay), (ax, ay + gap - 2)], fill=(80, 200, 120), width=2)
            draw.polygon(
                [(ax - 6, ay + gap - 6), (ax + 6, ay + gap - 6), (ax, ay + gap + 2)],
                fill=(80, 200, 120)
            )

        y_offset += card_height + gap

    # Footer
    draw.line([(32, y_offset + 8), (card_width - 32, y_offset + 8)], fill=(50, 50, 70), width=1)
    draw.text(
        (32, y_offset + 18),
        "DigitalAgEdu  ·  The Ohio State University  ·  ICICLE AI Institute  ·  NSF OAC 2112606",
        font=footer_font,
        fill=(80, 90, 110)
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    canvas.save(output_path)
    print(f"Overview saved to: {output_path}")
    return output_path


# ----------------------------
# Text summary (terminal)
# ----------------------------
def print_pipeline_overview():
    print("\n" + "=" * 70)
    print("  DigitalAgEdu — AI Pipeline Overview")
    print("=" * 70)
    print(
        "\n  You are about to build a real computer vision system that helps\n"
        "  farmers detect corn diseases from photos.\n\n"
        "  Here is every stage you will build, week by week:\n"
    )
    for stage in STAGES:
        print(f"  {'─' * 64}")
        print(f"  Stage {stage['number']}  {stage['symbol']}  {stage['name']}  [{stage['week']}]")
        print(f"  What:   {stage['what']}")
        print(f"  Why:    {stage['why']}")
        print(f"  Output: {stage['output']}")
    print(f"  {'─' * 64}")
    print("\n  Each week's starter code builds one of these stages.")
    print("  By Week 10, all stages connect into a single running pipeline.\n")


# ----------------------------
# Entry point
# ----------------------------
if __name__ == "__main__":
    print_pipeline_overview()

    image_paths = load_sample_images(DATASET_ROOT, n=SAMPLE_COUNT)

    if image_paths:
        print(f"\nLoaded {len(image_paths)} sample image(s) from dataset:\n")
        for p in image_paths:
            print(f"  [{get_class_from_path(p)}]  {os.path.basename(p)}")

        out = os.path.join(OUTPUT_DIR, "pipeline_overview.png")
        render_full_overview(image_paths, out)
        print(f"\nOpen {out} to see the visual overview.")
    else:
        print("\nNo images found at DATASET_ROOT — update the path at the top of this file.")
        print("The terminal overview above still runs without images.\n")