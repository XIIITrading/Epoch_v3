"""
Market Structure Calculator - Epoch Ticker Structure Module
Epoch Trading System v1 - XIII Trading LLC

Detects fractals, identifies BOS/ChoCH, and determines market direction.
Same calculation logic as Meridian Trading System.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import epoch_ticker_structure_config as config


class MarketStructureCalculator:
    """
    Calculates market structure (Bull/Bear) from OHLC data.
    """
    
    def __init__(self, fractal_length: int = None):
        """
        Initialize market structure calculator.
        
        Args:
            fractal_length: Number of bars on each side for fractal detection
        """
        self.length = fractal_length or config.FRACTAL_LENGTH
        self.p = int(self.length / 2)
    
    def _detect_fractals(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """
        Detect bullish and bearish fractals in the price data.
        
        Args:
            df: DataFrame with 'high' and 'low' columns
        
        Returns:
            Tuple of (bullish_fractals, bearish_fractals) as boolean Series
        """
        n = len(df)
        p = self.p
        
        bullf = pd.Series([False] * n, index=df.index)
        bearf = pd.Series([False] * n, index=df.index)
        
        if n < self.length:
            return bullf, bearf
        
        for i in range(p, n - p):
            # Bearish fractal (local high)
            before_lower = all(df['high'].iloc[i-j] < df['high'].iloc[i] for j in range(1, p+1))
            after_lower = all(df['high'].iloc[i+j] < df['high'].iloc[i] for j in range(1, p+1))
            
            if before_lower and after_lower:
                bearf.iloc[i] = True
            
            # Bullish fractal (local low)
            before_higher = all(df['low'].iloc[i-j] > df['low'].iloc[i] for j in range(1, p+1))
            after_higher = all(df['low'].iloc[i+j] > df['low'].iloc[i] for j in range(1, p+1))
            
            if before_higher and after_higher:
                bullf.iloc[i] = True
        
        return bullf, bearf
    
    def _calculate_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate market structure including fractals, breaks, and direction.
        
        Args:
            df: DataFrame with OHLC data
        
        Returns:
            DataFrame with added structure columns
        """
        bullf, bearf = self._detect_fractals(df)
        
        df = df.copy()
        df['bullish_fractal'] = bullf
        df['bearish_fractal'] = bearf
        df['upper_fractal_value'] = np.nan
        df['lower_fractal_value'] = np.nan
        df['upper_crossed'] = False
        df['lower_crossed'] = False
        df['structure'] = 0
        df['structure_label'] = ''
        df['bull_continuation_high'] = np.nan  # Track highest high in bull structure
        df['bear_continuation_low'] = np.nan   # Track lowest low in bear structure
        
        upper_value = None
        upper_crossed = False
        lower_value = None
        lower_crossed = False
        current_structure = 0
        bull_continuation_high = None
        bear_continuation_low = None
        
        for i in range(len(df)):
            close = df['close'].iloc[i]
            high = df['high'].iloc[i]
            low = df['low'].iloc[i]
            
            if bearf.iloc[i]:
                upper_value = df['high'].iloc[i]
                upper_crossed = False
            
            if bullf.iloc[i]:
                lower_value = df['low'].iloc[i]
                lower_crossed = False
            
            df.loc[df.index[i], 'upper_fractal_value'] = upper_value
            df.loc[df.index[i], 'lower_fractal_value'] = lower_value
            
            if upper_value is not None and not upper_crossed:
                if close > upper_value:
                    if current_structure == -1:
                        df.loc[df.index[i], 'structure_label'] = 'ChoCH'
                    else:
                        df.loc[df.index[i], 'structure_label'] = 'BOS'
                    current_structure = 1
                    upper_crossed = True
                    # Initialize continuation high when structure turns bullish
                    bull_continuation_high = high
            
            if lower_value is not None and not lower_crossed:
                if close < lower_value:
                    if current_structure == 1:
                        df.loc[df.index[i], 'structure_label'] = 'ChoCH'
                    else:
                        df.loc[df.index[i], 'structure_label'] = 'BOS'
                    current_structure = -1
                    lower_crossed = True
                    # Initialize continuation low when structure turns bearish
                    bear_continuation_low = low
            
            # Update continuation levels while in structure
            if current_structure == 1:  # Bull structure
                if bull_continuation_high is None or high > bull_continuation_high:
                    bull_continuation_high = high
            elif current_structure == -1:  # Bear structure
                if bear_continuation_low is None or low < bear_continuation_low:
                    bear_continuation_low = low
            
            df.loc[df.index[i], 'structure'] = current_structure
            df.loc[df.index[i], 'upper_crossed'] = upper_crossed
            df.loc[df.index[i], 'lower_crossed'] = lower_crossed
            df.loc[df.index[i], 'bull_continuation_high'] = bull_continuation_high
            df.loc[df.index[i], 'bear_continuation_low'] = bear_continuation_low
        
        return df
    
    def calculate(self, df: pd.DataFrame) -> Dict:
        """
        Calculate market structure from OHLC data.
        
        Args:
            df: DataFrame with columns: timestamp, open, high, low, close, volume
        
        Returns:
            Dictionary with:
            - direction: 1 (Bull), -1 (Bear), or 0 (Neutral)
            - direction_label: 'BULL', 'BEAR', or 'NEUTRAL'
            - strong_level: Invalidation level (ChoCH level)
            - weak_level: Continuation level (last opposite fractal)
            - df: Full DataFrame with all calculations
        """
        if df is None or df.empty:
            return self._error_result("Empty or None DataFrame")
        
        required = ['open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required):
            return self._error_result(f"Missing required columns")
        
        if len(df) < 50:
            return self._error_result(f"Insufficient bars: {len(df)}")
        
        df_calc = self._calculate_structure(df)
        current_direction = int(df_calc['structure'].iloc[-1])
        
        breaks = df_calc[df_calc['structure_label'] != '']
        
        if len(breaks) == 0:
            return {
                'direction': 0,
                'direction_label': 'NEUTRAL',
                'last_structure_break': None,
                'last_structure_label': None,
                'strong_level': None,
                'weak_level': None,
                'df': df_calc
            }
        
        last_break = breaks.iloc[-1]
        last_break_idx = breaks.index[-1]
        
        strong_level = None
        weak_level = None
        
        if current_direction == 1:  # Bull
            # Strong (invalidation) = lower fractal (support that if broken = ChoCH)
            strong_level = df_calc['lower_fractal_value'].iloc[-1]
            # Weak (continuation) = highest high since structure turned bullish
            weak_level = df_calc['bull_continuation_high'].iloc[-1]
        elif current_direction == -1:  # Bear
            # Strong (invalidation) = upper fractal (resistance that if broken = ChoCH)
            strong_level = df_calc['upper_fractal_value'].iloc[-1]
            # Weak (continuation) = lowest low since structure turned bearish
            weak_level = df_calc['bear_continuation_low'].iloc[-1]
        
        return {
            'direction': current_direction,
            'direction_label': config.STRUCTURE_LABELS.get(current_direction, 'NEUTRAL'),
            'last_structure_break': last_break_idx,
            'last_structure_label': last_break['structure_label'],
            'strong_level': strong_level,
            'weak_level': weak_level,
            'df': df_calc
        }
    
    def _error_result(self, message: str) -> Dict:
        """Return error result structure."""
        if config.VERBOSE:
            print(f"   ⚠️  Market Structure Error: {message}")
        return {
            'direction': None,
            'direction_label': 'ERROR',
            'last_structure_break': None,
            'last_structure_label': None,
            'strong_level': None,
            'weak_level': None,
            'df': None,
            'error': message
        }