"""
DOW AI - Command Line Interface
Epoch Trading System v1 - XIII Trading LLC

Click-based CLI for entry/exit analysis.
"""
import click
from datetime import datetime
import pytz
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import MODELS, TIMEZONE
from analysis.aggregator import AnalysisAggregator
from output.terminal import (
    print_entry_analysis,
    print_exit_analysis,
    print_error,
    print_models,
    print_welcome
)


@click.group()
def cli():
    """DOW AI Trading Assistant - Entry/Exit Analysis"""
    pass


@cli.command()
@click.argument('ticker')
@click.argument('direction', type=click.Choice(['long', 'short'], case_sensitive=False))
@click.argument('zone', type=click.Choice(['primary', 'secondary'], case_sensitive=False))
@click.option('-d', '--datetime', 'dt_str', default=None, help='Historical datetime: YYYY-MM-DD-HH:MM')
def entry(ticker: str, direction: str, zone: str, dt_str: str):
    """
    Analyze potential entry.

    Arguments:
        TICKER:    Stock symbol (e.g., NVDA, TSLA)
        DIRECTION: Trade direction - 'long' or 'short'
        ZONE:      Zone type - 'primary' or 'secondary'

    Examples:
        entry NVDA long secondary
        entry TSLA short primary
        entry MSFT long primary -d 2024-12-03-10:30

    The tool will:
        1. Read zone data from Analysis worksheet
        2. Run 10-step analysis for the specified direction
        3. Calculate the appropriate EPCH model (01/02/03/04)
        4. Present results with model classification
    """
    try:
        # Parse datetime if provided
        analysis_dt = None
        if dt_str:
            try:
                tz = pytz.timezone(TIMEZONE)
                # Support both formats: "YYYY-MM-DD HH:MM" and "YYYY-MM-DD-HH:MM"
                if ' ' in dt_str:
                    analysis_dt = tz.localize(datetime.strptime(dt_str, "%Y-%m-%d %H:%M"))
                else:
                    # Convert YYYY-MM-DD-HH:MM to datetime
                    analysis_dt = tz.localize(datetime.strptime(dt_str, "%Y-%m-%d-%H:%M"))
            except ValueError:
                print_error(f"Invalid datetime format. Use: YYYY-MM-DD-HH:MM (got: '{dt_str}')")
                return

        # Run analysis
        aggregator = AnalysisAggregator(verbose=True)
        result = aggregator.run_entry_analysis(
            ticker=ticker.upper(),
            direction=direction.lower(),
            zone_type=zone.lower(),
            analysis_datetime=analysis_dt
        )

        if 'error' in result:
            print_error(result['error'])
            return

        print_entry_analysis(result)

    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()


@cli.command()
@click.argument('ticker')
@click.argument('action', type=click.Choice(['sell', 'cover'], case_sensitive=False))
@click.argument('zone', type=click.Choice(['primary', 'secondary'], case_sensitive=False))
@click.option('-d', '--datetime', 'dt_str', default=None, help='Historical datetime: YYYY-MM-DD-HH:MM')
def exit(ticker: str, action: str, zone: str, dt_str: str):
    """
    Analyze potential exit.

    Arguments:
        TICKER: Stock symbol (e.g., NVDA, TSLA)
        ACTION: Exit action - 'sell' (close long) or 'cover' (close short)
        ZONE:   Zone type - 'primary' or 'secondary'

    Examples:
        exit TSLA sell primary
        exit NVDA cover secondary -d 2024-12-03-14:45
    """
    try:
        # Parse datetime if provided
        analysis_dt = None
        if dt_str:
            try:
                tz = pytz.timezone(TIMEZONE)
                # Support both formats: "YYYY-MM-DD HH:MM" and "YYYY-MM-DD-HH:MM"
                if ' ' in dt_str:
                    analysis_dt = tz.localize(datetime.strptime(dt_str, "%Y-%m-%d %H:%M"))
                else:
                    # Convert YYYY-MM-DD-HH:MM to datetime
                    analysis_dt = tz.localize(datetime.strptime(dt_str, "%Y-%m-%d-%H:%M"))
            except ValueError:
                print_error(f"Invalid datetime format. Use: YYYY-MM-DD-HH:MM (got: '{dt_str}')")
                return

        # Run analysis
        aggregator = AnalysisAggregator(verbose=True)
        result = aggregator.run_exit_analysis(
            ticker=ticker.upper(),
            exit_action=action.lower(),
            zone_type=zone.lower(),
            analysis_datetime=analysis_dt
        )

        if 'error' in result:
            print_error(result['error'])
            return

        print_exit_analysis(result)

    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()


@cli.command()
def models():
    """List available trading models."""
    print_models()


@cli.command()
def welcome():
    """Show welcome message and help."""
    print_welcome()


if __name__ == '__main__':
    cli()
