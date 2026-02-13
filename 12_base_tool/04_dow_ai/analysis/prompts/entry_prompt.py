"""
Entry analysis prompt template for Claude.
Zone-anchored analysis with auto-calculated model.
"""

ENTRY_PROMPT_TEMPLATE = """You are DOW, an AI trading assistant for the Epoch Trading System.

TRADE REQUEST:
- Ticker: {ticker}
- Direction: {direction}
- Zone Type: {zone_type}
- Current Price: ${current_price:.2f}
- Analysis Time: {analysis_time}

ZONE DATA (from Analysis worksheet):
- Zone ID: {zone_id}
- Zone Direction: {zone_direction}
- Range: ${zone_low:.2f} - ${zone_high:.2f}
- HVN POC: ${hvn_poc:.2f}
- Target: ${target:.2f} ({target_id})
- R:R: {r_r}

PRICE-TO-ZONE:
- Position: {price_position}
- {price_description}

MODEL CLASSIFICATION:
- Code: {model_code}
- Name: {model_name}
- Type: {trade_type}
- Logic: {model_logic}

MARKET STRUCTURE:
{structure_table}

VOLUME ANALYSIS:
{volume_section}

CANDLESTICK PATTERNS:
{patterns_list}

SUPPORTING LEVELS:
- D1 ATR: ${atr:.2f}
- HVN POCs: {hvn_pocs}
- Camarilla: {camarilla}

SMA ANALYSIS (Steps 8-9):
{sma_section}

VWAP ANALYSIS (Step 10):
{vwap_section}

---

RUN THE 10-STEP ANALYSIS for this {direction} trade:

STEP 1: HTF Structure (H4 → H1) - Is structure aligned with {direction}?
STEP 2: HTF % Within Strong/Weak - Where is price relative to HTF levels?
STEP 3: MTF Structure (M15 → M5) - Is momentum aligned with {direction}?
STEP 4: MTF % Within Strong/Weak - Where is price relative to MTF levels?
STEP 5: Volume ROC - Is volume elevated or waning?
STEP 6: Volume Delta (M15/M5) - Is delta supporting {direction}?
STEP 7: CVD Direction + Trend - Accumulation or distribution?
STEP 8: SMA9/SMA21 Alignment - In line with {direction}?
STEP 9: SMA Spread - Diverging (momentum) or converging (exhaustion)?
STEP 10: VWAP Location - Price above or below VWAP?

Provide output in this EXACT format:

══════════════════════════════════════════════════════════════════════════════
                         10-STEP MARKET ANALYSIS
══════════════════════════════════════════════════════════════════════════════

STEP 1: HIGHER TIMEFRAME STRUCTURE (H4 → H1)
────────────────────────────────────────────────────────────────────────────────
[Analysis with specific levels]
Status: [✓/⚠/✗] [Assessment]
To Align: [What needs to happen]

[Continue for all 10 steps...]

══════════════════════════════════════════════════════════════════════════════
                              ALIGNMENT SUMMARY
══════════════════════════════════════════════════════════════════════════════

SCORECARD:
  Step 1  (HTF Structure):     [✓/⚠/✗]
  Step 2  (HTF Levels):        [✓/⚠/✗]
  Step 3  (MTF Structure):     [✓/⚠/✗]
  Step 4  (MTF Levels):        [✓/⚠/✗]
  Step 5  (Volume ROC):        [✓/⚠/✗]
  Step 6  (Volume Delta):      [✓/⚠/✗]
  Step 7  (CVD):               [✓/⚠/✗]
  Step 8  (SMA Alignment):     [✓/⚠/✗]
  Step 9  (SMA Momentum):      [✓/⚠/✗]
  Step 10 (VWAP):              [✓/⚠/✗]
  ─────────────────────────────────────
  TOTAL ALIGNED: X/10

══════════════════════════════════════════════════════════════════════════════
                         SETUP CLASSIFICATION: {model_code}
══════════════════════════════════════════════════════════════════════════════

CONFIDENCE: [HIGH/MEDIUM/LOW] (X/10)

KEY ALIGNMENTS:
• [Bullet points of aligned factors]

KEY CONCERNS:
• [Bullet points of concerns]

CONFIRMATION TRIGGERS:
• [What needs to happen for entry]

INVALIDATION:
• [Specific level that invalidates the setup]

TRADE PLAN (if confirmed):
  Entry Zone: ${zone_low:.2f} - ${zone_high:.2f}
  Stop:       $X.XX [reasoning]
  Target 1:   ${target:.2f} ({target_id})
  Target 2:   $X.XX [next level]
  R:R:        {r_r}

══════════════════════════════════════════════════════════════════════════════
                              CURRENT ACTION
══════════════════════════════════════════════════════════════════════════════

[One clear sentence: What should trader do RIGHT NOW]
"""


def build_entry_prompt(
    ticker: str,
    direction: str,
    zone_type: str,
    zone: dict,
    price_zone_rel: dict,
    model_code: str,
    model_name: str,
    trade_type: str,
    current_price: float,
    analysis_time: str,
    structure: dict,
    volume,
    m5_volume,
    m15_volume,
    patterns: dict,
    atr: float,
    hvn_pocs: list,
    camarilla: dict,
    all_zones: dict,
    smas: dict = None,
    vwap_result = None,
) -> str:
    """Build the complete entry prompt."""

    # Format structure table
    structure_lines = ["TF       Direction    Strong Level    Weak Level    Last Break"]
    for tf in ['H4', 'H1', 'M15', 'M5']:
        if tf in structure:
            s = structure[tf]
            strong = f"${s.strong_level:.2f}" if s.strong_level else "N/A"
            weak = f"${s.weak_level:.2f}" if s.weak_level else "N/A"
            break_info = f"{s.last_break} @ ${s.last_break_price:.2f}" if s.last_break and s.last_break_price else "N/A"
            structure_lines.append(f"{tf:<8} {s.direction:<12} {strong:<15} {weak:<13} {break_info}")
    structure_table = "\n".join(structure_lines)

    # Format volume section
    volume_lines = [
        f"M1 Delta (5-bar):  {volume.delta_5bar:+,.0f} ({volume.delta_signal})",
        f"M1 Volume ROC:     {volume.roc_percent:+.1f}% vs 20-bar avg ({volume.roc_signal})",
        f"M1 CVD Trend:      {volume.cvd_trend}"
    ]
    if m5_volume:
        volume_lines.append(f"M5 Delta (5-bar):  {m5_volume.delta_5bar:+,.0f} ({m5_volume.delta_signal})")
    if m15_volume:
        volume_lines.append(f"M15 Delta (5-bar): {m15_volume.delta_5bar:+,.0f} ({m15_volume.delta_signal})")
    volume_section = "\n".join(volume_lines)

    # Format patterns
    pattern_lines = []
    for tf in ['M5', 'M15', 'H1']:
        if tf in patterns and patterns[tf]:
            for p in patterns[tf][:2]:
                ago = "current bar" if p.bars_ago == 0 else f"{p.bars_ago} bars ago"
                pattern_lines.append(f"{tf}: {p.pattern} @ ${p.price:.2f} ({ago})")
    patterns_list = "\n".join(pattern_lines) if pattern_lines else "None detected"

    # Format supporting levels
    hvn_str = ", ".join([f"${p:.2f}" for p in hvn_pocs[:5]]) if hvn_pocs else "N/A"
    cam_str = f"S3: ${camarilla.get('d1_s3', 0):.2f}, R3: ${camarilla.get('d1_r3', 0):.2f}" if camarilla else "N/A"

    # =========================================
    # FORMAT SMA SECTION (Steps 8-9)
    # =========================================
    sma_lines = []
    if smas:
        for tf in ['M5', 'M15']:
            if tf in smas and smas[tf] is not None:
                s = smas[tf]
                alignment_emoji = "✅" if (
                    (direction == 'long' and s.alignment == 'BULLISH') or
                    (direction == 'short' and s.alignment == 'BEARISH')
                ) else "⚠️" if s.alignment == 'NEUTRAL' else "❌"
                sma_lines.append(
                    f"  {tf}: SMA9 ${s.sma9:.2f} | SMA21 ${s.sma21:.2f} | "
                    f"{s.alignment} {alignment_emoji} | Spread: {s.spread_trend}"
                )
    sma_section = "\n".join(sma_lines) if sma_lines else "  DATA NOT AVAILABLE"

    # =========================================
    # FORMAT VWAP SECTION (Step 10)
    # =========================================
    if vwap_result and hasattr(vwap_result, 'vwap') and vwap_result.vwap and vwap_result.vwap > 0:
        vwap_aligned = (
            (direction == 'long' and vwap_result.side == 'ABOVE') or
            (direction == 'short' and vwap_result.side == 'BELOW')
        )
        vwap_emoji = "✅" if vwap_aligned else "⚠️" if vwap_result.side == 'AT' else "❌"
        vwap_section = (
            f"  Session VWAP: ${vwap_result.vwap:.2f}\n"
            f"  Price vs VWAP: {vwap_result.side} by ${abs(vwap_result.price_diff):.2f} "
            f"({vwap_result.price_pct:+.2f}%) {vwap_emoji}"
        )
    else:
        vwap_section = "  DATA NOT AVAILABLE"

    # Model logic description
    zone_dir = zone['direction']
    if trade_type == 'continuation':
        model_logic = f"Trading WITH zone direction ({zone_dir}) = Continuation"
    else:
        model_logic = f"Trading AGAINST zone direction ({zone_dir}) = Reversal"

    # Handle None target
    target_val = zone.get('target') if zone.get('target') is not None else 0.0

    return ENTRY_PROMPT_TEMPLATE.format(
        ticker=ticker,
        direction=direction.upper(),
        zone_type=zone_type.upper(),
        current_price=current_price,
        analysis_time=analysis_time,
        zone_id=zone['zone_id'],
        zone_direction=zone['direction'],
        zone_low=zone['zone_low'],
        zone_high=zone['zone_high'],
        hvn_poc=zone['hvn_poc'],
        target=target_val,
        target_id=zone.get('target_id', 'N/A'),
        r_r=zone.get('r_r', 'N/A'),
        price_position=price_zone_rel['position'],
        price_description=price_zone_rel['description'],
        model_code=model_code,
        model_name=model_name,
        trade_type=trade_type.upper(),
        model_logic=model_logic,
        structure_table=structure_table,
        volume_section=volume_section,
        patterns_list=patterns_list,
        atr=atr,
        hvn_pocs=hvn_str,
        camarilla=cam_str,
        sma_section=sma_section,
        vwap_section=vwap_section,
    )
