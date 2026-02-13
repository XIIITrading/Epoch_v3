"""
Epoch Trading System - Image Exporter
Composite image builder for social media platforms.
Uses Pillow to combine 6 Plotly chart PNGs with GrowthHub branding.
Charts: Daily, H1, M15, M5 Entry, M1 Action, M1 Ramp-Up.
"""

import tempfile
import os
import logging
from pathlib import Path
from datetime import date
from typing import Optional, List, Tuple

import plotly.graph_objects as go
from PIL import Image, ImageDraw, ImageFont

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from config import EXPORT_SIZES, BRANDING, EXPORT_DIR, BRAND_COLORS, FONTS_DIR, TV_COLORS
from models.highlight import HighlightTrade
from ui.rampup_table import (
    INDICATOR_LABELS,
    _fmt_candle_range, _fmt_vol_delta, _fmt_vol_roc, _fmt_sma,
    _fmt_structure,
    _color_candle_range, _color_vol_delta, _color_vol_roc, _color_sma,
    _color_structure,
)

logger = logging.getLogger(__name__)

# Chart render dimensions for export (higher quality)
EXPORT_CHART_WIDTH = 1800
EXPORT_CHART_HEIGHT = 500
EXPORT_SCALE = 2

# Branding watermark
WATERMARK_HANDLE = '@codycsilva'


def _get_brand_font(role: str, size: int) -> ImageFont.FreeTypeFont:
    """
    Get a GrowthHub brand font by role.

    Roles:
        'header'  - Anton Bold (H1 headers)
        'title'   - Roboto Condensed (H2/H3 titles)
        'body'    - Roboto Regular (body text)
        'accent'  - Playfair Display Italic (accents)

    Falls back to system fonts if brand fonts not found.
    """
    role_to_file = {
        'header': BRANDING.get('font_header', ''),
        'title': BRANDING.get('font_title', ''),
        'body': BRANDING.get('font_body', ''),
        'accent': BRANDING.get('font_accent', ''),
    }

    font_file = role_to_file.get(role, '')
    if font_file and FONTS_DIR.exists():
        font_path = FONTS_DIR / font_file
        if font_path.exists():
            try:
                return ImageFont.truetype(str(font_path), size)
            except OSError:
                pass

    # Fallback to system fonts
    fallbacks = ['seguisb.ttf', 'trebucbd.ttf', 'arialbd.ttf'] if role in ('header', 'title') else ['segoeui.ttf', 'trebuc.ttf', 'arial.ttf']
    for name in fallbacks:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _render_fig_to_image(
    fig: go.Figure,
    width: int = EXPORT_CHART_WIDTH,
    height: int = EXPORT_CHART_HEIGHT,
) -> Optional[Image.Image]:
    """Render Plotly figure to PIL Image via kaleido."""
    fd, temp_path = tempfile.mkstemp(suffix='.png')
    os.close(fd)

    try:
        fig.write_image(
            temp_path, format='png',
            width=width, height=height, scale=EXPORT_SCALE,
        )
        img = Image.open(temp_path).copy()
        return img
    except Exception as e:
        logger.error(f"Error rendering chart to image: {e}")
        return None
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def _draw_header(
    draw: ImageDraw.Draw,
    canvas_width: int,
    header_height: int,
    highlight: HighlightTrade,
):
    """Draw GrowthHub branded header with trade info."""
    # Header background — charcoal
    draw.rectangle(
        [0, 0, canvas_width, header_height],
        fill=BRANDING['header_bg'],
    )

    # Accent line at bottom — forest green
    draw.rectangle(
        [0, header_height - 3, canvas_width, header_height],
        fill=BRANDING['header_accent'],
    )

    # Fonts — GrowthHub typography
    font_brand = _get_brand_font('header', 28)     # Anton for "GROWTH HUB"
    font_handle = _get_brand_font('body', 13)       # Roboto for handle
    font_ticker = _get_brand_font('header', 22)     # Anton for ticker
    font_info = _get_brand_font('title', 16)        # Roboto Condensed for details
    font_detail = _get_brand_font('body', 14)       # Roboto for outcome
    font_watermark = _get_brand_font('body', 11)

    # Left: Brand name (Anton, cream)
    draw.text((20, 8), BRANDING['title'], fill=BRAND_COLORS['cream'], font=font_brand)
    draw.text((20, 42), BRANDING['subtitle'], fill=BRAND_COLORS['sage'], font=font_handle)

    # Center: Trade info — ticker (Anton, cream) + details (Roboto Condensed, terracotta/sage)
    bull_color = BRAND_COLORS['sage']
    bear_color = BRAND_COLORS['terracotta']
    dir_color = bull_color if highlight.direction == 'LONG' else bear_color

    ticker_text = highlight.ticker
    detail_parts = f"  |  {highlight.date}  |  {highlight.direction}  |  {highlight.model or ''}"

    bbox_ticker = draw.textbbox((0, 0), ticker_text, font=font_ticker)
    ticker_w = bbox_ticker[2] - bbox_ticker[0]
    bbox_detail = draw.textbbox((0, 0), detail_parts, font=font_info)
    detail_w = bbox_detail[2] - bbox_detail[0]
    total_w = ticker_w + detail_w
    x_start = (canvas_width - total_w) // 2

    draw.text((x_start, 14), ticker_text, fill=BRAND_COLORS['cream'], font=font_ticker)
    draw.text((x_start + ticker_w, 16), detail_parts, fill=dir_color, font=font_info)

    # Below center: outcome (Roboto, light stone)
    outcome_color = bull_color if highlight.is_winner else bear_color
    pnl_str = f"{highlight.pnl_r:+.2f}R" if highlight.pnl_r else ""
    detail = f"{highlight.star_display} Achieved  |  {pnl_str}  |  {highlight.exit_reason}"
    bbox2 = draw.textbbox((0, 0), detail, font=font_detail)
    text_w2 = bbox2[2] - bbox2[0]
    x_center2 = (canvas_width - text_w2) // 2
    draw.text((x_center2, 46), detail, fill=outcome_color, font=font_detail)

    # Right: Rating (Anton, forest green)
    rating_text = f"R{highlight.max_r_achieved}"
    font_rating = _get_brand_font('header', 34)
    bbox3 = draw.textbbox((0, 0), rating_text, font=font_rating)
    text_w3 = bbox3[2] - bbox3[0]
    draw.text((canvas_width - text_w3 - 25, 10), rating_text,
              fill=BRAND_COLORS['forest_green'], font=font_rating)

    # Watermark handle (bottom-right of header, muted)
    bbox_wm = draw.textbbox((0, 0), WATERMARK_HANDLE, font=font_watermark)
    wm_w = bbox_wm[2] - bbox_wm[0]
    draw.text((canvas_width - wm_w - 25, header_height - 18),
              WATERMARK_HANDLE, fill='#4A4E49', font=font_watermark)


def _draw_watermark(draw: ImageDraw.Draw, canvas_w: int, canvas_h: int):
    """Draw subtle watermark in bottom-right corner."""
    font_wm = _get_brand_font('body', 12)
    bbox = draw.textbbox((0, 0), WATERMARK_HANDLE, font=font_wm)
    wm_w = bbox[2] - bbox[0]
    draw.text((canvas_w - wm_w - 15, canvas_h - 20),
              WATERMARK_HANDLE, fill='#3A3E39', font=font_wm)


def _render_indicator_table(
    rampup_df: pd.DataFrame,
    width: int,
    height: int,
) -> Optional[Image.Image]:
    """Render M1 ramp-up indicator table as a PIL Image.

    Rows = 7 indicators, Columns = bar times.
    Reuses formatters/colors from rampup_table.py.
    """
    if rampup_df is None or rampup_df.empty:
        return None

    bg_color = '#131722'
    border_color = '#2A2E39'
    header_bg = '#1E222D'
    text_muted = '#787B86'

    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        font = ImageFont.truetype("consola.ttf", 11)
        font_bold = ImageFont.truetype("consolab.ttf", 11)
        font_header = ImageFont.truetype("consolab.ttf", 10)
    except (IOError, OSError):
        font = ImageFont.load_default()
        font_bold = font
        font_header = font

    num_bars = len(rampup_df)
    num_ind = len(INDICATOR_LABELS)

    # Layout
    label_w = 70       # Left column for indicator names
    row_h = height // (num_ind + 1)  # +1 for header row
    col_w = (width - label_w) / max(num_bars, 1)

    # Cell value/color lookup
    def _cell(ind_name, row):
        if ind_name == 'Candle %':
            return _fmt_candle_range(row.get('candle_range_pct')), _color_candle_range(row.get('candle_range_pct'))
        elif ind_name == 'Vol Delta':
            return _fmt_vol_delta(row.get('vol_delta')), _color_vol_delta(row.get('vol_delta'))
        elif ind_name == 'Vol ROC':
            return _fmt_vol_roc(row.get('vol_roc')), _color_vol_roc(row.get('vol_roc'))
        elif ind_name == 'SMA':
            return _fmt_sma(row.get('sma_spread'), row.get('close')), _color_sma(row.get('sma_spread'))
        elif ind_name == 'M5 Struct':
            return _fmt_structure(row.get('m5_structure')), _color_structure(row.get('m5_structure'))
        elif ind_name == 'M15 Struct':
            return _fmt_structure(row.get('m15_structure')), _color_structure(row.get('m15_structure'))
        elif ind_name == 'H1 Struct':
            return _fmt_structure(row.get('h1_structure')), _color_structure(row.get('h1_structure'))
        return '-', text_muted

    # Draw header row (time labels)
    for col_idx, (_, row) in enumerate(rampup_df.iterrows()):
        bt = row.get('bar_time')
        if bt and hasattr(bt, 'strftime'):
            label = bt.strftime('%H:%M')
        else:
            label = str(bt)[:5] if bt else '-'
        x = label_w + int(col_idx * col_w)
        # Header background
        draw.rectangle([x, 0, x + int(col_w), row_h], fill=header_bg, outline=border_color)
        # Center text
        bbox = draw.textbbox((0, 0), label, font=font_header)
        tw = bbox[2] - bbox[0]
        tx = x + (int(col_w) - tw) // 2
        ty = (row_h - (bbox[3] - bbox[1])) // 2
        draw.text((tx, ty), label, fill=text_muted, font=font_header)

    # Draw indicator label column header
    draw.rectangle([0, 0, label_w, row_h], fill=header_bg, outline=border_color)

    # Draw rows
    for row_idx, ind_name in enumerate(INDICATOR_LABELS):
        y = (row_idx + 1) * row_h

        # Row label
        draw.rectangle([0, y, label_w, y + row_h], fill=header_bg, outline=border_color)
        bbox = draw.textbbox((0, 0), ind_name, font=font_bold)
        tw = bbox[2] - bbox[0]
        tx = (label_w - tw) // 2
        ty = y + (row_h - (bbox[3] - bbox[1])) // 2
        draw.text((tx, ty), ind_name, fill=text_muted, font=font_bold)

        # Data cells
        for col_idx, (_, data_row) in enumerate(rampup_df.iterrows()):
            value, color = _cell(ind_name, data_row)
            x = label_w + int(col_idx * col_w)

            draw.rectangle([x, y, x + int(col_w), y + row_h], fill=bg_color, outline=border_color)

            bbox = draw.textbbox((0, 0), value, font=font)
            tw = bbox[2] - bbox[0]
            tx = x + (int(col_w) - tw) // 2
            ty = y + (row_h - (bbox[3] - bbox[1])) // 2
            draw.text((tx, ty), value, fill=color, font=font)

    return img


def _build_instagram_image(
    top_fig: Optional[go.Figure],
    bottom_fig: go.Figure,
    canvas_w: int,
    canvas_h: int,
    split_ratio: float = 0.5,
) -> Optional[Image.Image]:
    """
    Build a single Instagram reel image (1080x1920) with top/bottom chart split.
    No header. If top_fig is None, top half is black.

    Args:
        top_fig: Plotly figure for top half, or None for black
        bottom_fig: Plotly figure for bottom half
        canvas_w: Image width (1080)
        canvas_h: Image height (1920)
        split_ratio: Fraction of canvas for top section (default 0.5)

    Returns:
        PIL Image or None on failure
    """
    top_h = int(canvas_h * split_ratio)
    bottom_h = canvas_h - top_h
    bg_color = '#000000'

    # Render charts at canvas width for best quality
    bottom_img = _render_fig_to_image(bottom_fig, width=canvas_w, height=bottom_h)
    if bottom_img is None:
        logger.error("Failed to render bottom chart for Instagram")
        return None

    top_img = None
    if top_fig is not None:
        top_img = _render_fig_to_image(top_fig, width=canvas_w, height=top_h)
        if top_img is None:
            logger.error("Failed to render top chart for Instagram")
            return None

    canvas = Image.new('RGB', (canvas_w, canvas_h), color=bg_color)

    # Top half: chart or black
    if top_img is not None:
        resized_top = top_img.resize((canvas_w, top_h), Image.LANCZOS)
        canvas.paste(resized_top, (0, 0))

    # Bottom half: chart
    resized_bottom = bottom_img.resize((canvas_w, bottom_h), Image.LANCZOS)
    canvas.paste(resized_bottom, (0, top_h))

    # Watermark
    draw = ImageDraw.Draw(canvas)
    _draw_watermark(draw, canvas_w, canvas_h)

    return canvas


def export_highlight_image(
    daily_fig: go.Figure,
    h1_fig: go.Figure,
    m15_fig: go.Figure,
    m5_entry_fig: go.Figure,
    m1_fig: go.Figure,
    m1_rampup_fig: go.Figure,
    highlight: HighlightTrade,
    platform: str,
    output_dir: Optional[Path] = None,
    h1_prior_fig: Optional[go.Figure] = None,
    rampup_df=None,
) -> Optional[List[Path]]:
    """
    Export composite marketing image(s) for a platform.

    Instagram: 2 images (H1 prior + M15|M1)
    Discord:   H1 prior (25%) + M15|M1 (50%) + indicator table (25%)
    X/StockTwits: H1 prior (30%) + M15|M1 (70%)

    Args:
        daily_fig: Daily context chart
        h1_fig: H1 context chart
        m15_fig: M15 context chart
        m5_entry_fig: M5 Entry chart
        m1_fig: M1 Action chart
        m1_rampup_fig: M1 Ramp-Up chart
        highlight: HighlightTrade data
        platform: 'twitter', 'instagram', 'stocktwits', 'discord'
        output_dir: Output directory (defaults to EXPORT_DIR)
        h1_prior_fig: H1 chart sliced to hour before entry
        rampup_df: DataFrame of M1 indicator bars (for Discord table)

    Returns:
        List of exported file paths, or None on failure
    """
    if platform not in EXPORT_SIZES:
        logger.error(f"Unknown platform: {platform}")
        return None

    out_dir = output_dir or EXPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    canvas_w, canvas_h = EXPORT_SIZES[platform]
    date_str = highlight.date.strftime('%Y%m%d')

    # -----------------------------------------------------------------
    # INSTAGRAM: 3 separate reel images (1080x1920), no header
    # -----------------------------------------------------------------
    if platform == 'instagram':
        # Image 1: Top=black (35%), Bottom=H1 Prior Context (65%)
        h1_for_ig = h1_prior_fig if h1_prior_fig is not None else h1_fig
        img1 = _build_instagram_image(None, h1_for_ig, canvas_w, canvas_h, split_ratio=0.35)
        # Image 2: Top=M15, Bottom=M1 Action (50/50)
        img2 = _build_instagram_image(m15_fig, m1_fig, canvas_w, canvas_h, split_ratio=0.5)

        results = []
        for idx, img in enumerate([img1, img2], start=1):
            if img is None:
                logger.error(f"Failed to build Instagram image {idx}")
                continue
            filename = f"{highlight.ticker}_{date_str}_{platform}_{idx}.png"
            output_path = out_dir / filename
            try:
                img.save(str(output_path), 'PNG', quality=95)
                logger.info(f"Exported: {output_path}")
                results.append(output_path)
            except Exception as e:
                logger.error(f"Error saving Instagram image {idx}: {e}")

        return results if results else None

    # -----------------------------------------------------------------
    # DISCORD: 3 images (1920x1080 each)
    #   Each page: top chart 45% / charcoal caption gap 10% / bottom chart 45%
    #   Page 1: Daily + H1 Pre-trade
    #   Page 2: M1 Ramp-Up Chart + M1 Ramp-Up Indicator Table
    #   Page 3: M15 + M1 Action
    # -----------------------------------------------------------------
    if platform == 'discord':
        h1_for_export = h1_prior_fig if h1_prior_fig is not None else h1_fig

        # Render all chart images
        daily_img = _render_fig_to_image(daily_fig)
        h1_img = _render_fig_to_image(h1_for_export)
        rampup_chart_img = _render_fig_to_image(m1_rampup_fig)
        m15_img = _render_fig_to_image(m15_fig)
        m1_img = _render_fig_to_image(m1_fig)

        if not all([daily_img, h1_img, m15_img, m1_img]):
            logger.error("Failed to render one or more charts")
            return None

        # Layout constants — consistent 45/10/45 split
        inner_pad = 8
        content_w = canvas_w - inner_pad * 2
        full_h = canvas_h - inner_pad * 2
        section_h = int(full_h * 0.45)
        gap_h = full_h - section_h * 2       # ~10% charcoal caption space
        charcoal = BRAND_COLORS['charcoal']   # #1C1C1C

        def _build_discord_page(top_img, bottom_img):
            """Compose a single Discord page: top 45% | charcoal gap 10% | bottom 45%."""
            page = Image.new('RGB', (canvas_w, canvas_h), color='#000000')
            draw = ImageDraw.Draw(page)

            # Top chart (45%)
            if top_img is not None:
                resized = top_img.resize((content_w, section_h), Image.LANCZOS)
                page.paste(resized, (inner_pad, inner_pad))

            # Charcoal caption gap (10%) — full width
            gap_y = inner_pad + section_h
            draw.rectangle([0, gap_y, canvas_w, gap_y + gap_h], fill=charcoal)

            # Bottom chart/table (45%)
            if bottom_img is not None:
                resized = bottom_img.resize((content_w, section_h), Image.LANCZOS)
                page.paste(resized, (inner_pad, inner_pad + section_h + gap_h))

            return page

        # Page 1: Daily + H1
        img1 = _build_discord_page(daily_img, h1_img)

        # Page 2: M1 Ramp-Up Chart + Indicator Table
        rampup_table_img = _render_indicator_table(rampup_df, content_w, section_h)
        img2 = _build_discord_page(rampup_chart_img, rampup_table_img)

        # Page 3: M15 + M1 Action
        img3 = _build_discord_page(m15_img, m1_img)

        # Save all 3 images
        results = []
        for idx, img in enumerate([img1, img2, img3], start=1):
            filename = f"{highlight.ticker}_{date_str}_{platform}_{idx}.png"
            output_path = out_dir / filename
            try:
                img.save(str(output_path), 'PNG', quality=95)
                logger.info(f"Exported: {output_path}")
                results.append(output_path)
            except Exception as e:
                logger.error(f"Error saving Discord image {idx}: {e}")

        return results if results else None

    # -----------------------------------------------------------------
    # X / TWITTER / STOCKTWITS: H1 prior (30%) + M15|M1 (70%), no header
    # -----------------------------------------------------------------

    # Render the 3 charts we need
    h1_for_export = h1_prior_fig if h1_prior_fig is not None else h1_fig
    h1_img = _render_fig_to_image(h1_for_export)
    m15_img = _render_fig_to_image(m15_fig)
    m1_img = _render_fig_to_image(m1_fig)

    if not all([h1_img, m15_img, m1_img]):
        logger.error("Failed to render one or more charts")
        return None

    # Create canvas — no header
    canvas = Image.new('RGB', (canvas_w, canvas_h), color='#000000')

    inner_pad = 8
    area_y = inner_pad
    area_h = canvas_h - inner_pad * 2
    padding = 4

    # Top 40%: H1 prior (full width)
    top_h = int(area_h * 0.40)
    h1_resized = h1_img.resize((canvas_w - inner_pad * 2, top_h), Image.LANCZOS)
    canvas.paste(h1_resized, (inner_pad, area_y))

    # Bottom 60%: M15 (left) + M1 (right) side by side
    bottom_y = area_y + top_h + padding
    bottom_h = area_h - top_h - padding
    half_w = (canvas_w - inner_pad * 2 - padding) // 2

    m15_resized = m15_img.resize((half_w, bottom_h), Image.LANCZOS)
    m1_resized = m1_img.resize((half_w, bottom_h), Image.LANCZOS)

    canvas.paste(m15_resized, (inner_pad, bottom_y))
    canvas.paste(m1_resized, (inner_pad + half_w + padding, bottom_y))

    # Save
    filename = f"{highlight.ticker}_{date_str}_{platform}.png"
    output_path = out_dir / filename

    try:
        canvas.save(str(output_path), 'PNG', quality=95)
        logger.info(f"Exported: {output_path}")
        return [output_path]
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        return None


def export_batch(
    charts_data: List[Tuple[go.Figure, go.Figure, go.Figure, go.Figure, go.Figure, go.Figure, HighlightTrade]],
    platform: str,
    output_dir: Optional[Path] = None,
    progress_callback=None,
) -> List[Path]:
    """
    Export multiple highlights for a platform.

    Args:
        charts_data: List of (daily, h1, m15, m5_entry, m1, m1_rampup, highlight) tuples
        platform: Platform name
        output_dir: Output directory
        progress_callback: Optional callable(current, total)

    Returns:
        List of exported file paths
    """
    results = []
    total = len(charts_data)

    for i, (daily, h1, m15, m5, m1, m1r, hl) in enumerate(charts_data):
        paths = export_highlight_image(daily, h1, m15, m5, m1, m1r, hl, platform, output_dir)
        if paths:
            results.extend(paths)
        if progress_callback:
            progress_callback(i + 1, total)

    return results
