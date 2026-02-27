"""
Ticker Selection Exporter
Epoch Trading System v2.0 - XIII Trading LLC

Persists daily ticker selections to Supabase ticker_analysis table.
"""

import psycopg2
from datetime import date
from typing import Dict, List, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_CONFIG


def save_ticker_selections(session_date: date, selections: List[Dict]) -> Dict:
    """
    Save 4 ticker selections to Supabase.

    Args:
        session_date: Trading date
        selections: List of dicts with keys:
            ticker, direction, structure_d1, structure_h1,
            primary_scenario, secondary_scenario

    Returns:
        Dict with 'success' bool and 'message' string
    """
    if not selections:
        return {"success": False, "message": "No selections provided"}

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Ensure table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ticker_analysis (
                date DATE NOT NULL,
                ticker VARCHAR(10) NOT NULL,
                direction VARCHAR(10) NOT NULL,
                structure_d1 TEXT,
                structure_h1 TEXT,
                primary_scenario TEXT,
                secondary_scenario TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (date, ticker)
            );
        """)

        count = 0
        for sel in selections:
            ticker = sel.get("ticker", "").strip().upper()
            if not ticker:
                continue

            cursor.execute("""
                INSERT INTO ticker_analysis (
                    date, ticker, direction,
                    structure_d1, structure_h1,
                    primary_scenario, secondary_scenario,
                    updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (date, ticker) DO UPDATE SET
                    direction = EXCLUDED.direction,
                    structure_d1 = EXCLUDED.structure_d1,
                    structure_h1 = EXCLUDED.structure_h1,
                    primary_scenario = EXCLUDED.primary_scenario,
                    secondary_scenario = EXCLUDED.secondary_scenario,
                    updated_at = NOW()
            """, (
                session_date,
                ticker,
                sel.get("direction", "BEAR"),
                sel.get("structure_d1", ""),
                sel.get("structure_h1", ""),
                sel.get("primary_scenario", ""),
                sel.get("secondary_scenario", ""),
            ))
            count += 1

        conn.commit()
        cursor.close()
        conn.close()

        return {"success": True, "message": f"Saved {count} ticker selections"}

    except Exception as e:
        return {"success": False, "message": f"Database error: {str(e)}"}


def load_ticker_selections(session_date: date) -> List[Dict]:
    """
    Load ticker selections for a given date.

    Args:
        session_date: Trading date

    Returns:
        List of selection dicts, or empty list
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ticker, direction, structure_d1, structure_h1,
                   primary_scenario, secondary_scenario
            FROM ticker_analysis
            WHERE date = %s
            ORDER BY ticker
        """, (session_date,))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return [
            {
                "ticker": row[0],
                "direction": row[1],
                "structure_d1": row[2] or "",
                "structure_h1": row[3] or "",
                "primary_scenario": row[4] or "",
                "secondary_scenario": row[5] or "",
            }
            for row in rows
        ]

    except Exception:
        return []
