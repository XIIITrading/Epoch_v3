"""
Discord Post Generator
Epoch Trading System v2.0 - XIII Trading LLC

Generates styled PNG images and formatted text for Discord/Instagram posting.
"""

from PIL import Image, ImageDraw, ImageFont
from datetime import date, datetime
from typing import Dict, List, Optional
from pathlib import Path
import textwrap


# =============================================================================
# COLORS (matching Epoch dark theme)
# =============================================================================
BG_COLOR = (10, 10, 10)           # #0a0a0a
HEADER_BG = (15, 52, 96)          # #0f3460
ROW_BG = (10, 10, 10)             # #0a0a0a
ROW_ALT_BG = (20, 20, 20)         # #141414
BORDER_COLOR = (42, 42, 74)       # #2a2a4a
TEXT_PRIMARY = (232, 232, 232)     # #e8e8e8
TEXT_SECONDARY = (160, 160, 160)   # #a0a0a0
TEXT_MUTED = (112, 112, 112)       # #707070
BULL_COLOR = (38, 166, 154)        # #26a69a
BEAR_COLOR = (239, 83, 80)        # #ef5350
BULL_BG = (20, 60, 55)            # dark green background for badge
BEAR_BG = (70, 25, 25)            # dark red background for badge
BRAND_COLOR = (160, 160, 160)     # #a0a0a0

# =============================================================================
# FONTS
# =============================================================================
FONT_DIR = "C:/Windows/Fonts"

def _load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a font with fallback."""
    try:
        return ImageFont.truetype(f"{FONT_DIR}/{name}", size)
    except OSError:
        return ImageFont.load_default()

FONT_TITLE = _load_font("segoeuib.ttf", 22)
FONT_SUBTITLE = _load_font("segoeui.ttf", 16)
FONT_HEADER = _load_font("segoeuib.ttf", 14)
FONT_TICKER = _load_font("segoeuib.ttf", 16)
FONT_BODY = _load_font("segoeui.ttf", 13)
FONT_BADGE = _load_font("segoeuib.ttf", 14)
FONT_LABEL = _load_font("segoeuib.ttf", 12)
FONT_BRAND = _load_font("segoeui.ttf", 12)


# =============================================================================
# TEXT WRAPPING
# =============================================================================
def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.Draw) -> List[str]:
    """Wrap text to fit within max_width pixels."""
    if not text:
        return [""]

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines if lines else [""]


# =============================================================================
# PNG GENERATION
# =============================================================================
def generate_analysis_png(
    selections: List[Dict],
    session_date: date,
    output_dir: Optional[str] = None,
) -> str:
    """
    Generate a styled dark-themed analysis table as PNG.

    Args:
        selections: List of ticker selection dicts
        session_date: Trading date
        output_dir: Output directory (defaults to 01_application/exports/)

    Returns:
        Path to the saved PNG file
    """
    if output_dir is None:
        output_dir = str(Path(__file__).parent.parent / "exports")

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # --- Layout constants ---
    IMG_WIDTH = 1400
    PADDING = 30
    CONTENT_WIDTH = IMG_WIDTH - (PADDING * 2)

    # Column widths
    COL_TICKER = 100
    COL_DIRECTION = 90
    COL_SCENARIO = 280
    COL_STRUCTURE = CONTENT_WIDTH - COL_TICKER - COL_DIRECTION - (COL_SCENARIO * 2) - 4  # borders

    HEADER_HEIGHT = 70
    COL_HEADER_HEIGHT = 36
    ROW_PADDING_V = 14
    ROW_PADDING_H = 12

    # --- Pre-calculate row heights ---
    # Create a temp image for text measurement
    temp_img = Image.new("RGB", (IMG_WIDTH, 100))
    temp_draw = ImageDraw.Draw(temp_img)

    row_data = []
    for sel in selections:
        # Wrap structure text (D1 + H1 combined with line break)
        d1_text = f"D1: {sel.get('structure_d1', '')}"
        h1_text = f"H1: {sel.get('structure_h1', '')}"

        d1_lines = _wrap_text(d1_text, FONT_BODY, COL_STRUCTURE - (ROW_PADDING_H * 2), temp_draw)
        h1_lines = _wrap_text(h1_text, FONT_BODY, COL_STRUCTURE - (ROW_PADDING_H * 2), temp_draw)

        # Wrap scenario text
        pri_lines = _wrap_text(
            sel.get("primary_scenario", ""), FONT_BODY, COL_SCENARIO - (ROW_PADDING_H * 2), temp_draw
        )
        sec_lines = _wrap_text(
            sel.get("secondary_scenario", ""), FONT_BODY, COL_SCENARIO - (ROW_PADDING_H * 2), temp_draw
        )

        # Calculate line height
        bbox = temp_draw.textbbox((0, 0), "Tg", font=FONT_BODY)
        line_height = (bbox[3] - bbox[1]) + 4

        # Structure height: D1 lines + gap + H1 lines
        structure_lines = len(d1_lines) + 1 + len(h1_lines)
        scenario_lines = max(len(pri_lines), len(sec_lines))
        content_lines = max(structure_lines, scenario_lines, 3)
        row_height = (content_lines * line_height) + (ROW_PADDING_V * 2)

        row_data.append({
            "sel": sel,
            "d1_lines": d1_lines,
            "h1_lines": h1_lines,
            "pri_lines": pri_lines,
            "sec_lines": sec_lines,
            "line_height": line_height,
            "row_height": row_height,
        })

    # --- Calculate total image height ---
    total_row_height = sum(r["row_height"] for r in row_data)
    FOOTER_HEIGHT = 40
    IMG_HEIGHT = HEADER_HEIGHT + COL_HEADER_HEIGHT + total_row_height + FOOTER_HEIGHT + (PADDING * 2)

    # --- Create final image ---
    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # --- Draw header ---
    draw.rectangle(
        [PADDING, PADDING, IMG_WIDTH - PADDING, PADDING + HEADER_HEIGHT],
        fill=HEADER_BG
    )

    # Title text
    draw.text(
        (PADDING + 20, PADDING + 14),
        "XIII TRADING",
        font=FONT_TITLE, fill=TEXT_PRIMARY
    )

    # Subtitle
    draw.text(
        (PADDING + 200, PADDING + 18),
        "Daily Market Analysis",
        font=FONT_SUBTITLE, fill=TEXT_SECONDARY
    )

    # Date + timestamp on right
    timestamp_str = f"{session_date.strftime('%m/%d/%Y')}  {datetime.now().strftime('%I:%M %p')}"
    bbox = draw.textbbox((0, 0), timestamp_str, font=FONT_SUBTITLE)
    ts_width = bbox[2] - bbox[0]
    draw.text(
        (IMG_WIDTH - PADDING - 20 - ts_width, PADDING + 18),
        timestamp_str, font=FONT_SUBTITLE, fill=TEXT_SECONDARY
    )

    # --- Draw column headers ---
    y = PADDING + HEADER_HEIGHT
    col_x = [
        PADDING,
        PADDING + COL_TICKER + 1,
        PADDING + COL_TICKER + COL_STRUCTURE + 2,
        PADDING + COL_TICKER + COL_STRUCTURE + COL_SCENARIO + 3,
        PADDING + COL_TICKER + COL_STRUCTURE + (COL_SCENARIO * 2) + 4,
    ]

    # Header background
    draw.rectangle(
        [PADDING, y, IMG_WIDTH - PADDING, y + COL_HEADER_HEIGHT],
        fill=(20, 35, 60)
    )

    headers = ["Ticker", "Structure", "Primary", "Secondary", "Direction"]
    header_widths = [COL_TICKER, COL_STRUCTURE, COL_SCENARIO, COL_SCENARIO, COL_DIRECTION]

    for i, (header, width) in enumerate(zip(headers, header_widths)):
        draw.text(
            (col_x[i] + ROW_PADDING_H, y + 10),
            header, font=FONT_HEADER, fill=TEXT_SECONDARY
        )

    # Header border
    draw.line(
        [(PADDING, y + COL_HEADER_HEIGHT), (IMG_WIDTH - PADDING, y + COL_HEADER_HEIGHT)],
        fill=BORDER_COLOR, width=1
    )

    # --- Draw ticker rows ---
    y = PADDING + HEADER_HEIGHT + COL_HEADER_HEIGHT

    for idx, rd in enumerate(row_data):
        sel = rd["sel"]
        row_h = rd["row_height"]
        line_h = rd["line_height"]

        # Alternating row background
        bg = ROW_ALT_BG if idx % 2 == 1 else ROW_BG
        draw.rectangle(
            [PADDING, y, IMG_WIDTH - PADDING, y + row_h],
            fill=bg
        )

        content_y = y + ROW_PADDING_V

        # Ticker name
        draw.text(
            (col_x[0] + ROW_PADDING_H, content_y),
            sel.get("ticker", "").upper(),
            font=FONT_TICKER, fill=TEXT_PRIMARY
        )

        # Structure (D1 + H1)
        struct_y = content_y
        for line in rd["d1_lines"]:
            draw.text((col_x[1] + ROW_PADDING_H, struct_y), line, font=FONT_BODY, fill=TEXT_PRIMARY)
            struct_y += line_h
        struct_y += line_h  # gap between D1 and H1
        for line in rd["h1_lines"]:
            draw.text((col_x[1] + ROW_PADDING_H, struct_y), line, font=FONT_BODY, fill=TEXT_PRIMARY)
            struct_y += line_h

        # Primary scenario
        pri_y = content_y
        for line in rd["pri_lines"]:
            draw.text((col_x[2] + ROW_PADDING_H, pri_y), line, font=FONT_BODY, fill=TEXT_PRIMARY)
            pri_y += line_h

        # Secondary scenario
        sec_y = content_y
        for line in rd["sec_lines"]:
            draw.text((col_x[3] + ROW_PADDING_H, sec_y), line, font=FONT_BODY, fill=TEXT_PRIMARY)
            sec_y += line_h

        # Direction badge
        direction = sel.get("direction", "BEAR").upper()
        badge_color = BULL_COLOR if direction == "BULL" else BEAR_COLOR
        badge_bg = BULL_BG if direction == "BULL" else BEAR_BG

        badge_x = col_x[4] + ROW_PADDING_H
        badge_y = content_y
        badge_w = COL_DIRECTION - (ROW_PADDING_H * 2)
        badge_h = 26

        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
            radius=4, fill=badge_bg
        )

        # Center badge text
        bbox = draw.textbbox((0, 0), direction, font=FONT_BADGE)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text(
            (badge_x + (badge_w - text_w) // 2, badge_y + (badge_h - text_h) // 2 - 1),
            direction, font=FONT_BADGE, fill=badge_color
        )

        # Row separator
        draw.line(
            [(PADDING, y + row_h), (IMG_WIDTH - PADDING, y + row_h)],
            fill=BORDER_COLOR, width=1
        )

        # Column separators within row
        for cx in col_x[1:]:
            draw.line([(cx - 1, y), (cx - 1, y + row_h)], fill=BORDER_COLOR, width=1)

        y += row_h

    # --- Draw footer ---
    draw.text(
        (PADDING + 10, y + 12),
        "XIII Trading LLC",
        font=FONT_BRAND, fill=TEXT_MUTED
    )

    ts_full = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bbox = draw.textbbox((0, 0), ts_full, font=FONT_BRAND)
    draw.text(
        (IMG_WIDTH - PADDING - 10 - (bbox[2] - bbox[0]), y + 12),
        ts_full, font=FONT_BRAND, fill=TEXT_MUTED
    )

    # --- Draw outer border ---
    draw.rectangle(
        [PADDING, PADDING, IMG_WIDTH - PADDING, y],
        outline=BORDER_COLOR, width=1
    )

    # --- Save ---
    filename = f"analysis_{session_date.strftime('%Y-%m-%d')}_{datetime.now().strftime('%H%M%S')}.png"
    filepath = str(Path(output_dir) / filename)
    img.save(filepath, "PNG", quality=95)

    return filepath


# =============================================================================
# DISCORD TEXT
# =============================================================================
def generate_discord_text(selections: List[Dict], session_date: date) -> str:
    """
    Generate formatted Discord markdown text.

    Args:
        selections: List of ticker selection dicts
        session_date: Trading date

    Returns:
        Formatted Discord markdown string
    """
    timestamp = datetime.now().strftime("%I:%M %p")
    lines = [
        f"**XIII Trading — Daily Analysis — {session_date.strftime('%m/%d/%Y')} {timestamp}**",
        "",
    ]

    for sel in selections:
        ticker = sel.get("ticker", "").upper()
        direction = sel.get("direction", "BEAR").upper()

        if not ticker:
            continue

        emoji = "\U0001f534" if direction == "BEAR" else "\U0001f7e2"  # red/green circle
        lines.append(f"**{ticker}** {emoji} {direction}")

        d1 = sel.get("structure_d1", "").strip()
        h1 = sel.get("structure_h1", "").strip()
        if d1:
            lines.append(f"D1: {d1}")
        if h1:
            lines.append(f"H1: {h1}")

        pri = sel.get("primary_scenario", "").strip()
        sec = sel.get("secondary_scenario", "").strip()
        if pri:
            lines.append(f"> Primary: {pri}")
        if sec:
            lines.append(f"> Secondary: {sec}")

        lines.append("")

    return "\n".join(lines).strip()
