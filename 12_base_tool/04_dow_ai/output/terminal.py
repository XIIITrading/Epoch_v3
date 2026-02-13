"""
DOW AI - Rich Terminal Output
Epoch Trading System v1 - XIII Trading LLC

Formatted terminal output using Rich library.
"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from datetime import datetime
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

console = Console()


def print_header(ticker: str, mode: str, direction: str, model: str, analysis_time: datetime):
    """Print analysis header."""
    title = f"DOW ANALYSIS: {ticker} | {mode.upper()} {direction.upper()} | MODEL: {model}"
    timestamp = analysis_time.strftime("%Y-%m-%d %H:%M:%S ET")

    console.print()
    console.print("=" * 70, style="bold blue")
    console.print(title, style="bold white")
    console.print(f"Timestamp: {timestamp}", style="dim")
    console.print("=" * 70, style="bold blue")


def print_section(title: str):
    """Print section divider."""
    console.print()
    console.print("-" * 70, style="dim")
    console.print(title, style="bold cyan")
    console.print("-" * 70, style="dim")


def print_current_price(price: float):
    """Print current price prominently."""
    console.print(f"\nCURRENT PRICE: ${price:.2f}", style="bold yellow")


def print_zone_context(zone: Optional[Dict]):
    """Print zone information."""
    print_section("ZONE CONTEXT")

    if not zone:
        console.print("No active zone identified", style="dim red")
        return

    console.print(f"Active Zone:     {zone.get('rank', 'N/A')} | ${zone['zone_low']:.2f} - ${zone['zone_high']:.2f} | HVN POC: ${zone['hvn_poc']:.2f}")
    console.print(f"Zone Score:      {zone.get('score', 'N/A')} | Confluences: {zone.get('confluences', 'N/A')}")

    if zone.get('target'):
        console.print(f"Target:          ${zone['target']:.2f}")


def print_structure_table(structure: Dict):
    """Print market structure table."""
    print_section("MARKET STRUCTURE")

    table = Table(box=box.SIMPLE)
    table.add_column("TF", style="cyan", width=6)
    table.add_column("Direction", width=12)
    table.add_column("Strong Level", width=14)
    table.add_column("Weak Level", width=14)
    table.add_column("Last Break", width=12)

    for tf in ['M5', 'M15', 'H1', 'H4']:
        if tf in structure:
            s = structure[tf]

            # Color direction
            if s.direction == "BULL":
                dir_style = "green"
            elif s.direction == "BEAR":
                dir_style = "red"
            else:
                dir_style = "yellow"

            direction = Text(s.direction, style=dir_style)

            strong = f"${s.strong_level:.2f}" if s.strong_level else "N/A"
            weak = f"${s.weak_level:.2f}" if s.weak_level else "N/A"

            if s.last_break:
                arrow = "^" if s.direction == "BULL" else "v"
                break_text = f"{s.last_break} {arrow}"
            else:
                break_text = "N/A"

            table.add_row(tf, direction, strong, weak, break_text)

    console.print(table)


def print_volume_analysis(volume):
    """Print volume analysis section."""
    print_section("VOLUME ANALYSIS")

    # Delta
    if volume.delta_signal == "Bullish":
        delta_style = "green"
    elif volume.delta_signal == "Bearish":
        delta_style = "red"
    else:
        delta_style = "yellow"

    console.print(f"Volume Delta (5-bar):    {volume.delta_5bar:+,.0f} ({volume.delta_signal})", style=delta_style)

    # ROC
    if volume.roc_signal == "Above Avg":
        roc_style = "green"
    elif volume.roc_signal == "Below Avg":
        roc_style = "red"
    else:
        roc_style = "yellow"

    console.print(f"Volume ROC:              {volume.roc_percent:+.1f}% ({volume.roc_signal})", style=roc_style)

    # CVD
    if volume.cvd_trend == "Rising":
        cvd_style = "green"
    elif volume.cvd_trend == "Falling":
        cvd_style = "red"
    else:
        cvd_style = "yellow"

    console.print(f"CVD Trend:               {volume.cvd_trend}", style=cvd_style)


def print_patterns(patterns: Dict):
    """Print candlestick patterns."""
    print_section("CANDLESTICK PATTERNS")

    found = False
    for tf in ['M5', 'M15', 'H1']:
        if tf in patterns and patterns[tf]:
            for p in patterns[tf][:2]:  # Max 2 per TF
                ago = "current bar" if p.bars_ago == 0 else f"{p.bars_ago} bars ago"

                if p.direction == "bullish":
                    style = "green"
                elif p.direction == "bearish":
                    style = "red"
                else:
                    style = "yellow"

                console.print(f"{tf}:  {p.pattern} @ ${p.price:.2f} ({ago})", style=style)
                found = True

    if not found:
        console.print("None detected", style="dim")


def print_claude_analysis(response: str):
    """Print Claude's analysis in a panel."""
    console.print()
    console.print("=" * 70, style="bold green")
    console.print("CLAUDE ANALYSIS", style="bold green")
    console.print("=" * 70, style="bold green")
    console.print()
    console.print(response)
    console.print()
    console.print("=" * 70, style="bold green")


def print_header_v2(ticker: str, direction: str, zone_type: str, model_code: str, model_name: str, analysis_time: datetime):
    """Print analysis header with auto-calculated model."""
    console.print()
    console.print("=" * 70, style="bold blue")
    console.print(f"DOW ANALYSIS: {ticker} {direction.upper()}", style="bold white")
    console.print(f"Zone: {zone_type.upper()} | Model: {model_code} ({model_name})", style="bold cyan")
    console.print(f"Timestamp: {analysis_time.strftime('%Y-%m-%d %H:%M:%S ET')}", style="dim")
    console.print("=" * 70, style="bold blue")


def print_zone_info(zone: dict, price_zone_rel: dict, current_price: float):
    """Print zone and price relationship."""
    print_section("ZONE & PRICE")

    # Zone details
    console.print(f"Zone ID:      {zone['zone_id']} ({zone['direction']})")
    console.print(f"Range:        ${zone['zone_low']:.2f} - ${zone['zone_high']:.2f}")
    console.print(f"HVN POC:      ${zone['hvn_poc']:.2f}")
    target_val = zone.get('target')
    if target_val:
        console.print(f"Target:       ${target_val:.2f} ({zone.get('target_id', 'N/A')})")
    else:
        console.print(f"Target:       N/A")
    console.print(f"R:R:          {zone.get('r_r', 'N/A')}")

    console.print()

    # Price relationship
    position = price_zone_rel['position']
    if position == 'ABOVE':
        style = "yellow"
    elif position == 'BELOW':
        style = "yellow"
    else:
        style = "green"

    console.print(f"Current:      ${current_price:.2f}", style="bold")
    console.print(f"Position:     {position} - {price_zone_rel['description']}", style=style)


def print_model_classification(model_code: str, model_name: str, trade_type: str, zone_direction: str, trade_direction: str):
    """Print how model was determined."""
    print_section("MODEL CLASSIFICATION")

    console.print(f"Model:        {model_code} - {model_name}", style="bold cyan")
    console.print(f"Trade Type:   {trade_type.upper()}")
    console.print(f"Logic:        {trade_direction.upper()} trade into {zone_direction} zone = {trade_type}")


def print_entry_analysis(result: Dict[str, Any]):
    """Print complete entry analysis with new format."""

    # Check if using new format (has zone_type) or old format (has model)
    if 'zone_type' in result:
        # New format with auto-calculated model
        print_header_v2(
            result['ticker'],
            result['direction'],
            result['zone_type'],
            result['model_code'],
            result['model_name'],
            result['analysis_time']
        )

        # Zone and price info
        print_zone_info(
            result['zone'],
            result['price_zone_rel'],
            result['current_price']
        )

        # Model classification
        print_model_classification(
            result['model_code'],
            result['model_name'],
            result['trade_type'],
            result['zone']['direction'],
            result['direction']
        )

        # Structure table
        print_structure_table(result['structure'])

        # Volume analysis
        print_volume_analysis(result['volume'])

        # Multi-TF volume if available
        if result.get('m5_volume'):
            console.print(f"M5 Delta:            {result['m5_volume'].delta_5bar:+,.0f} ({result['m5_volume'].delta_signal})")
        if result.get('m15_volume'):
            console.print(f"M15 Delta:           {result['m15_volume'].delta_5bar:+,.0f} ({result['m15_volume'].delta_signal})")

        # Patterns
        if 'patterns' in result:
            print_patterns(result['patterns'])

        # =========================================
        # SMA & VWAP TABLE (Steps 8-10)
        # =========================================
        sma_vwap_table = Table(
            title="[bold cyan]SMA & VWAP Analysis (Steps 8-10)[/bold cyan]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold white"
        )
        sma_vwap_table.add_column("Indicator", style="cyan", width=12)
        sma_vwap_table.add_column("Value", style="white", width=20)
        sma_vwap_table.add_column("Alignment", style="white", width=15)
        sma_vwap_table.add_column("Status", style="white", width=15)

        # Get direction for alignment checking
        direction = result.get('direction', 'long')

        # SMA Data
        smas = result.get('smas', {})
        if smas:
            for tf in ['M5', 'M15']:
                if tf in smas and smas[tf] is not None:
                    s = smas[tf]
                    # Check alignment with trade direction
                    aligned = (
                        (direction == 'long' and s.alignment == 'BULLISH') or
                        (direction == 'short' and s.alignment == 'BEARISH')
                    )
                    status_style = "[green]ALIGNED[/green]" if aligned else (
                        "[yellow]NEUTRAL[/yellow]" if s.alignment == 'NEUTRAL' else "[red]OPPOSED[/red]"
                    )
                    sma_vwap_table.add_row(
                        f"{tf} SMA",
                        f"9: ${s.sma9:.2f} | 21: ${s.sma21:.2f}",
                        f"{s.alignment} ({s.spread_trend})",
                        status_style
                    )
        else:
            sma_vwap_table.add_row("SMA", "DATA NOT AVAILABLE", "-", "[dim]N/A[/dim]")

        # VWAP Data
        vwap = result.get('vwap')
        if vwap and hasattr(vwap, 'vwap') and vwap.vwap and vwap.vwap > 0:
            vwap_aligned = (
                (direction == 'long' and vwap.side == 'ABOVE') or
                (direction == 'short' and vwap.side == 'BELOW')
            )
            vwap_status = "[green]ALIGNED[/green]" if vwap_aligned else (
                "[yellow]AT VWAP[/yellow]" if vwap.side == 'AT' else "[red]OPPOSED[/red]"
            )
            sma_vwap_table.add_row(
                "VWAP",
                f"${vwap.vwap:.2f}",
                f"{vwap.side} (${abs(vwap.price_diff):.2f})",
                vwap_status
            )
        else:
            sma_vwap_table.add_row("VWAP", "DATA NOT AVAILABLE", "-", "[dim]N/A[/dim]")

        console.print(sma_vwap_table)
        console.print()

        # Claude analysis
        print_claude_analysis(result['claude_response'])
    else:
        # Old format for backwards compatibility
        print_header(
            result['ticker'],
            'ENTRY',
            result['direction'],
            result.get('model', 'N/A'),
            result['analysis_time']
        )

        print_current_price(result['current_price'])
        print_zone_context(result.get('zone'))
        print_structure_table(result['structure'])
        print_volume_analysis(result['volume'])
        if 'patterns' in result:
            print_patterns(result['patterns'])
        print_claude_analysis(result['claude_response'])


def print_exit_analysis(result: Dict[str, Any]):
    """Print complete exit analysis."""
    # Check if using new format (has zone_type) or old format (has model)
    if 'zone_type' in result:
        # New format
        print_header_v2(
            result['ticker'],
            result['exit_action'].upper(),
            result['zone_type'],
            result['model_code'],
            result['model_name'],
            result['analysis_time']
        )
    else:
        # Old format
        print_header(
            result['ticker'],
            'EXIT',
            result['exit_action'],
            result.get('model', 'N/A'),
            result['analysis_time']
        )

    print_current_price(result['current_price'])

    # Target info
    target = result.get('target_price', 0)
    if target and result['current_price']:
        distance = abs(target - result['current_price'])
        distance_pct = (distance / result['current_price']) * 100
        console.print(f"TARGET:          ${target:.2f} ({result.get('target_id', 'N/A')}) | {distance_pct:.1f}% away", style="bold")

    print_zone_context(result.get('zone'))
    print_structure_table(result['structure'])
    print_volume_analysis(result['volume'])
    if 'patterns' in result:
        print_patterns(result['patterns'])
    print_claude_analysis(result['claude_response'])


def print_error(message: str):
    """Print error message."""
    console.print(f"\n[bold red]ERROR:[/bold red] {message}")


def print_welcome():
    """Print welcome banner."""
    console.print()
    console.print("=" * 70, style="bold cyan")
    console.print("   DOW AI TRADING ASSISTANT", style="bold white")
    console.print("   Epoch Trading System v1 - XIII Trading LLC", style="dim")
    console.print("=" * 70, style="bold cyan")
    console.print()
    console.print("Commands:", style="bold")
    console.print("  entry [TICKER] [long/short] [primary/secondary]", style="cyan")
    console.print("  exit [TICKER] [sell/cover] [primary/secondary]", style="cyan")
    console.print("  models                                          - List models", style="cyan")
    console.print()
    console.print("Examples:", style="bold")
    console.print("  entry NVDA long secondary", style="dim")
    console.print("  entry TSLA short primary", style="dim")
    console.print("  entry MSFT long primary --datetime \"2024-12-03 10:30\"", style="dim")
    console.print()
    console.print("The tool auto-calculates the EPCH model (01/02/03/04) based on", style="dim")
    console.print("zone direction and trade direction.", style="dim")
    console.print()
    console.print("Type 'quit' or 'exit' to close", style="dim")
    console.print("=" * 70, style="bold cyan")


def print_models():
    """Print available models."""
    from config import MODELS

    console.print("\nAvailable Models:\n", style="bold")

    for model_id, info in MODELS.items():
        console.print(f"  [cyan]{model_id}[/cyan]: {info['name']}")
        console.print(f"         {info['description']}", style="dim")
        console.print()
