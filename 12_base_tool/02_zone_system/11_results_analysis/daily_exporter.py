"""
Module 10: Daily Exporter
Generates structured JSON for AI analysis of daily trading results.

UPDATED: V1.1 compatibility - Tier column included in zone analysis
"""
import json
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import asdict

from config import OUTPUT_DIR, MODEL_DESCRIPTIONS, TIER_DESCRIPTIONS
from excel_reader import (
    ExcelReader, Trade, NoTrade, ZoneData, MarketStructure,
    EntryEvent, ExitEvent, OptimalTrade
)
from polygon_fetcher import PolygonFetcher


class DailyExporter:
    """Exports daily trading data to structured JSON for AI analysis."""
    
    def __init__(self, target_date: str = None, skip_polygon: bool = False):
        self.target_date = target_date or date.today().strftime("%Y-%m-%d")
        self.skip_polygon = skip_polygon
        self.excel_reader = ExcelReader()
        self.polygon = PolygonFetcher() if not skip_polygon else None
    
    def _trade_to_dict(self, trade: Trade) -> Dict[str, Any]:
        """Convert Trade to dictionary for JSON (v2.3 format)."""
        return {
            "trade_id": trade.trade_id,      # v2.3
            "ticker": trade.ticker,
            "model": trade.model,
            "model_name": trade.model_name,
            "zone_type": trade.zone_type,
            "direction": trade.direction,
            "zone_high": trade.zone_high,
            "zone_low": trade.zone_low,
            "entry_price": trade.entry_price,
            "entry_time": trade.entry_time,
            "stop_price": trade.stop_price,
            "target_3r": trade.target_3r,    # v2.3: renamed
            "target_calc": trade.target_calc,
            "target_used": trade.target_used,  # v2.3
            "exit_price": trade.exit_price,
            "exit_time": trade.exit_time,
            "exit_reason": trade.exit_reason,
            "pnl_dollars": trade.pnl_dollars,
            "pnl_r": trade.pnl_r,
            "risk": trade.risk,              # v2.3
            "is_win": trade.is_win,
        }
    
    def _no_trade_to_dict(self, nt: NoTrade) -> Dict[str, Any]:
        """Convert NoTrade to dictionary for JSON."""
        return {
            "ticker": nt.ticker,
            "model": nt.model,
            "model_name": nt.model_name,
            "zone_type": nt.zone_type,
            "direction": nt.direction,
            "zone_high": nt.zone_high,
            "zone_low": nt.zone_low,
            "reason": nt.reason,
            "day_high": nt.day_high,
            "day_low": nt.day_low,
            "day_open": nt.day_open,
            "day_close": nt.day_close,
            "zone_touched": nt.zone_touched,
            "bars_in_zone": nt.bars_in_zone,
        }
    
    def _entry_event_to_dict(self, ee: EntryEvent) -> Dict[str, Any]:
        """Convert EntryEvent to dictionary for JSON."""
        return {
            "trade_id": ee.trade_id,
            # Price Position
            "entry_vwap": ee.entry_vwap,
            "entry_vs_vwap": ee.entry_vs_vwap,
            "entry_sma9": ee.entry_sma9,
            "entry_vs_sma9": ee.entry_vs_sma9,
            "entry_sma21": ee.entry_sma21,
            "entry_vs_sma21": ee.entry_vs_sma21,
            "sma9_vs_sma21": ee.sma9_vs_sma21,
            # Volume Analysis
            "entry_volume": ee.entry_volume,
            "avg_volume_5": ee.avg_volume_5,
            "volume_delta_pct": ee.volume_delta_pct,
            "volume_trend": ee.volume_trend,
            "relative_volume": ee.relative_volume,
            "prior_bar_qual": ee.prior_bar_qual,
            "vol_delta_class": ee.vol_delta_class,
            # Multi-Timeframe Structure
            "m5_structure": ee.m5_structure,
            "m15_structure": ee.m15_structure,
            "h1_structure": ee.h1_structure,
            "h4_structure": ee.h4_structure,
            "structure_align": ee.structure_align,
            "dominant_struct": ee.dominant_struct,
            # Health Score
            "health_score": ee.health_score,
            "health_max": ee.health_max,
            "health_pct": ee.health_pct,
            "health_label": ee.health_label,
            # Alignment Flags
            "vwap_aligned": ee.vwap_aligned,
            "trend_aligned": ee.trend_aligned,
            "structure_aligned": ee.structure_aligned,
            # Status
            "status": ee.status,
        }
    
    def _exit_events_to_dict(self, events: List[ExitEvent]) -> List[Dict[str, Any]]:
        """Convert list of ExitEvents to list of dictionaries for JSON."""
        return [
            {
                "event_seq": e.event_seq,
                "event_time": e.event_time,
                "bars_from_entry": e.bars_from_entry,
                "bars_from_mfe": e.bars_from_mfe,
                "event_type": e.event_type,
                "from_state": e.from_state,
                "to_state": e.to_state,
                "price_at_event": e.price_at_event,
                "r_at_event": round(e.r_at_event, 2),
                "health_score": e.health_score,
                "health_delta": e.health_delta,
                "vwap": e.vwap,
                "sma9": e.sma9,
                "sma21": e.sma21,
            }
            for e in events
        ]
    
    def _optimal_trade_to_dict(self, ot: OptimalTrade) -> Dict[str, Any]:
        """Convert OptimalTrade to dictionary for JSON."""
        return {
            "trade_id": ot.trade_id,
            "optimal_exit_price": ot.optimal_exit_price,
            "optimal_exit_time": ot.optimal_exit_time,
            "optimal_exit_reason": ot.optimal_exit_reason,
            "optimal_pnl_r": round(ot.optimal_pnl_r, 2),
            "mfe_price": ot.mfe_price,
            "mfe_time": ot.mfe_time,
            "mfe_r": round(ot.mfe_r, 2),
            "mae_price": ot.mae_price,
            "mae_time": ot.mae_time,
            "mae_r": round(ot.mae_r, 2),
            "capture_efficiency": round(ot.capture_efficiency, 2) if ot.capture_efficiency else None,
            "notes": ot.notes,
        }
    
    def _calculate_statistics(self, trades: List[Trade]) -> Dict[str, Any]:
        """Calculate trading statistics from trades."""
        if not trades:
            return {
                "overall": self._empty_stats(),
                "by_model": {},
                "by_direction": {},
                "by_zone_type": {},
                "by_tier": {},  # V1.1: Added tier breakdown
            }
        
        # Overall stats
        winning = [t for t in trades if t.is_win]
        losing = [t for t in trades if not t.is_win]
        
        total_r = sum(t.pnl_r for t in trades)
        win_r = [t.pnl_r for t in winning] if winning else [0]
        loss_r = [t.pnl_r for t in losing] if losing else [0]
        
        overall = {
            "total_trades": len(trades),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": len(winning) / len(trades) if trades else 0,
            "net_pnl_r": round(total_r, 2),
            "expectancy_r": round(total_r / len(trades), 3) if trades else 0,
            "largest_win_r": max(win_r) if winning else 0,
            "largest_loss_r": min(loss_r) if losing else 0,
            "avg_win_r": round(sum(win_r) / len(winning), 2) if winning else 0,
            "avg_loss_r": round(sum(loss_r) / len(losing), 2) if losing else 0,
        }
        
        # By model
        by_model = {}
        for model in set(t.model for t in trades):
            model_trades = [t for t in trades if t.model == model]
            model_wins = [t for t in model_trades if t.is_win]
            model_r = sum(t.pnl_r for t in model_trades)
            
            model_name = model_trades[0].model_name if model_trades else model
            
            by_model[model] = {
                "model_name": model_name,
                "trades": len(model_trades),
                "win_rate": round(len(model_wins) / len(model_trades), 2) if model_trades else 0,
                "net_r": round(model_r, 2),
                "expectancy_r": round(model_r / len(model_trades), 3) if model_trades else 0,
            }
        
        # By direction
        by_direction = {}
        for direction in set(t.direction for t in trades):
            dir_trades = [t for t in trades if t.direction == direction]
            dir_wins = [t for t in dir_trades if t.is_win]
            dir_r = sum(t.pnl_r for t in dir_trades)
            
            by_direction[direction] = {
                "trades": len(dir_trades),
                "wins": len(dir_wins),
                "net_r": round(dir_r, 2),
                "win_rate": round(len(dir_wins) / len(dir_trades), 2) if dir_trades else 0,
            }
        
        # By zone type
        by_zone_type = {}
        for zone_type in set(t.zone_type for t in trades):
            zone_trades = [t for t in trades if t.zone_type == zone_type]
            zone_wins = [t for t in zone_trades if t.is_win]
            zone_r = sum(t.pnl_r for t in zone_trades)
            
            by_zone_type[zone_type] = {
                "trades": len(zone_trades),
                "wins": len(zone_wins),
                "net_r": round(zone_r, 2),
                "win_rate": round(len(zone_wins) / len(zone_trades), 2) if zone_trades else 0,
            }
        
        return {
            "overall": overall,
            "by_model": by_model,
            "by_direction": by_direction,
            "by_zone_type": by_zone_type,
        }
    
    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty statistics structure."""
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "net_pnl_r": 0,
            "expectancy_r": 0,
            "largest_win_r": 0,
            "largest_loss_r": 0,
            "avg_win_r": 0,
            "avg_loss_r": 0,
        }
    
    def _build_zone_analysis(
        self, 
        zones: Dict[str, Dict[str, ZoneData]], 
        structures: Dict[str, MarketStructure],
        trades: List[Trade]
    ) -> Dict[str, Any]:
        """Build zone analysis section with flip zone detection (V1.1 with Tier)."""
        analysis = {}
        
        # Get traded tickers for flip zone detection
        traded_tickers = set(t.ticker for t in trades)
        
        # Track tier distribution
        tier_counts = {"T1": 0, "T2": 0, "T3": 0}
        
        for ticker, zone_data in zones.items():
            structure = structures.get(ticker)
            direction = structure.composite if structure else "Unknown"
            
            primary = zone_data.get("primary")
            secondary = zone_data.get("secondary")
            
            # Count tiers
            if primary and primary.tier:
                tier_counts[primary.tier] = tier_counts.get(primary.tier, 0) + 1
            if secondary and secondary.tier:
                tier_counts[secondary.tier] = tier_counts.get(secondary.tier, 0) + 1
            
            # Check for flip zone (traded against composite direction)
            ticker_trades = [t for t in trades if t.ticker == ticker]
            is_flip = False
            for t in ticker_trades:
                if direction.startswith("Bull") and t.direction == "SHORT":
                    is_flip = True
                elif direction.startswith("Bear") and t.direction == "LONG":
                    is_flip = True
            
            analysis[ticker] = {
                "direction": direction,
                "composite": direction,
                "primary_zone": {
                    "zone_high": primary.zone_high if primary else 0,
                    "zone_low": primary.zone_low if primary else 0,
                    "hvn_poc": primary.hvn_poc if primary else 0,
                    "tier": primary.tier if primary else "",  # V1.1
                    "tier_description": TIER_DESCRIPTIONS.get(primary.tier, "") if primary else "",  # V1.1
                    "target": primary.target if primary else 0,
                    "rr_ratio": primary.rr_ratio if primary else 0,
                } if primary else None,
                "secondary_zone": {
                    "zone_high": secondary.zone_high if secondary else 0,
                    "zone_low": secondary.zone_low if secondary else 0,
                    "hvn_poc": secondary.hvn_poc if secondary else 0,
                    "tier": secondary.tier if secondary else "",  # V1.1
                    "tier_description": TIER_DESCRIPTIONS.get(secondary.tier, "") if secondary else "",  # V1.1
                    "target": secondary.target if secondary else 0,
                    "rr_ratio": secondary.rr_ratio if secondary else 0,
                } if secondary else None,
                "is_flip_zone": is_flip,
                "price_action": None,
            }
        
        return analysis
    
    def _build_market_context(
        self, 
        structures: Dict[str, MarketStructure]
    ) -> Dict[str, Any]:
        """Build market context section."""
        spy = structures.get("SPY")
        
        # Count composite directions
        user_tickers = {k: v for k, v in structures.items() 
                       if k not in ["SPY", "QQQ", "VIX", "DIA", "IWM"]}
        
        bull_count = sum(1 for s in user_tickers.values() if s.composite.startswith("Bull"))
        bear_count = sum(1 for s in user_tickers.values() if s.composite.startswith("Bear"))
        neutral_count = len(user_tickers) - bull_count - bear_count
        
        # D1 and H4 alignment counts
        d1_bull = sum(1 for s in user_tickers.values() if s.d1_dir == "Bull")
        d1_bear = sum(1 for s in user_tickers.values() if s.d1_dir == "Bear")
        h4_bull = sum(1 for s in user_tickers.values() if s.h4_dir == "Bull")
        h4_bear = sum(1 for s in user_tickers.values() if s.h4_dir == "Bear")
        
        context = {
            "spy_direction": spy.composite if spy else "Unknown",
            "spy_open": 0,
            "spy_high": 0,
            "spy_low": 0,
            "spy_close": 0,
            "spy_volume": 0,
            "vix_level": None,
            "market_structure": {
                "tickers_count": len(user_tickers),
                "composite_bull": bull_count,
                "composite_bear": bear_count,
                "composite_neutral": neutral_count,
                "d1_alignment": {
                    "bull": d1_bull,
                    "bear": d1_bear,
                    "neutral": len(user_tickers) - d1_bull - d1_bear,
                },
                "h4_alignment": {
                    "bull": h4_bull,
                    "bear": h4_bear,
                    "neutral": len(user_tickers) - h4_bull - h4_bear,
                },
                "by_ticker": {
                    ticker: {
                        "composite": s.composite,
                        "d1_dir": s.d1_dir,
                        "h4_dir": s.h4_dir,
                        "h1_dir": s.h1_dir,
                        "m15_dir": s.m15_dir,
                    } for ticker, s in user_tickers.items()
                }
            }
        }
        
        return context
    
    def _run_validation_checks(
        self, 
        trades: List[Trade], 
        zones: Dict[str, Dict[str, ZoneData]],
        zone_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run validation checks and identify anomalies."""
        anomalies = []
        errors = []
        flip_zones = []
        
        for ticker, analysis in zone_analysis.items():
            if analysis.get("is_flip_zone"):
                flip_zones.append(ticker)
        
        # Check trade entries vs zone positions
        for trade in trades:
            zone_mid = (trade.zone_high + trade.zone_low) / 2 if trade.zone_high else 0
            if zone_mid > 0:
                distance_pct = abs(trade.entry_price - zone_mid) / zone_mid * 100
                if distance_pct > 5:
                    anomalies.append(
                        f"Entry ${trade.entry_price:.2f} is {distance_pct:.1f}% from zone midpoint - verify zone data"
                    )
        
        # V1.1: Check tier quality
        tier_warnings = []
        for ticker, zone_data in zones.items():
            primary = zone_data.get("primary")
            secondary = zone_data.get("secondary")
            
            if primary and primary.tier == "T3":
                tier_warnings.append(f"{ticker} primary zone is T3 (marginal quality)")
            if secondary and secondary.tier == "T3":
                tier_warnings.append(f"{ticker} secondary zone is T3 (marginal quality)")
        
        return {
            "flip_zones_detected": flip_zones,
            "flip_zone_count": len(flip_zones),
            "tier_warnings": tier_warnings,  # V1.1
            "anomalies": anomalies,
            "errors": errors,
            "total_issues": len(anomalies) + len(errors) + len(tier_warnings),
        }
    
    def _build_tier_summary(self, zones: Dict[str, Dict[str, ZoneData]]) -> Dict[str, Any]:
        """V1.1: Build tier quality summary."""
        tier_counts = {"T1": 0, "T2": 0, "T3": 0, "unknown": 0}
        
        for ticker, zone_data in zones.items():
            primary = zone_data.get("primary")
            secondary = zone_data.get("secondary")
            
            if primary:
                tier = primary.tier if primary.tier in tier_counts else "unknown"
                tier_counts[tier] += 1
            if secondary:
                tier = secondary.tier if secondary.tier in tier_counts else "unknown"
                tier_counts[tier] += 1
        
        total = sum(tier_counts.values())
        
        return {
            "total_zones": total,
            "by_tier": tier_counts,
            "t1_percentage": round(tier_counts["T1"] / total * 100, 1) if total else 0,
            "t2_percentage": round(tier_counts["T2"] / total * 100, 1) if total else 0,
            "t3_percentage": round(tier_counts["T3"] / total * 100, 1) if total else 0,
            "tier_descriptions": TIER_DESCRIPTIONS,
        }
    
    def _build_health_summary(self, entry_events: Dict[str, EntryEvent]) -> Dict[str, Any]:
        """Build summary of entry health scores."""
        if not entry_events:
            return {}
        
        scores = [ee.health_score for ee in entry_events.values() if ee.health_score is not None]
        labels = [ee.health_label for ee in entry_events.values() if ee.health_label]
        
        label_counts = {}
        for label in labels:
            label_counts[label] = label_counts.get(label, 0) + 1
        
        # Count alignment stats
        vwap_aligned = sum(1 for ee in entry_events.values() if ee.vwap_aligned)
        trend_aligned = sum(1 for ee in entry_events.values() if ee.trend_aligned)
        structure_aligned = sum(1 for ee in entry_events.values() if ee.structure_aligned)
        total = len(entry_events)
        
        return {
            "avg_health_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "min_health_score": min(scores) if scores else 0,
            "max_health_score": max(scores) if scores else 0,
            "by_label": label_counts,
            "vwap_aligned_pct": round(vwap_aligned / total * 100, 1) if total else 0,
            "trend_aligned_pct": round(trend_aligned / total * 100, 1) if total else 0,
            "structure_aligned_pct": round(structure_aligned / total * 100, 1) if total else 0,
        }
    
    def _build_efficiency_summary(self, optimal_trades: Dict[str, OptimalTrade]) -> Dict[str, Any]:
        """Build summary of capture efficiency from optimal trade analysis."""
        if not optimal_trades:
            return {}
        
        efficiencies = [
            ot.capture_efficiency 
            for ot in optimal_trades.values() 
            if ot.capture_efficiency is not None and ot.capture_efficiency > 0
        ]
        
        mfe_rs = [ot.mfe_r for ot in optimal_trades.values() if ot.mfe_r is not None]
        mae_rs = [ot.mae_r for ot in optimal_trades.values() if ot.mae_r is not None]
        optimal_rs = [ot.optimal_pnl_r for ot in optimal_trades.values() if ot.optimal_pnl_r is not None]
        
        return {
            "avg_capture_efficiency": round(sum(efficiencies) / len(efficiencies) * 100, 1) if efficiencies else 0,
            "avg_mfe_r": round(sum(mfe_rs) / len(mfe_rs), 2) if mfe_rs else 0,
            "avg_mae_r": round(sum(mae_rs) / len(mae_rs), 2) if mae_rs else 0,
            "avg_optimal_r": round(sum(optimal_rs) / len(optimal_rs), 2) if optimal_rs else 0,
            "total_potential_r": round(sum(optimal_rs), 2) if optimal_rs else 0,
        }
    
    def export(self) -> Dict[str, Any]:
        """Generate the complete daily export."""
        try:
            # Read Excel data
            trades = self.excel_reader.read_trades(self.target_date)
            no_trades = self.excel_reader.read_no_trades(self.target_date)
            zones = self.excel_reader.read_zones()
            structures = self.excel_reader.read_market_structure()
            
            # Read enrichment data (entry_events, exit_events, optimal_trade)
            entry_events = self.excel_reader.read_entry_events(self.target_date)
            exit_events = self.excel_reader.read_exit_events(self.target_date)
            optimal_trades = self.excel_reader.read_optimal_trades(self.target_date)
            
            # Build sections
            zone_analysis = self._build_zone_analysis(zones, structures, trades)
            market_context = self._build_market_context(structures)
            statistics = self._calculate_statistics(trades)
            validation = self._run_validation_checks(trades, zones, zone_analysis)
            tier_summary = self._build_tier_summary(zones)  # V1.1
            
            # Fetch Polygon data if enabled
            m5_data = {"summary": {}, "note": "Polygon data skipped"}
            if self.polygon:
                try:
                    # Get SPY data
                    spy_bars = self.polygon.get_daily_bars("SPY", self.target_date)
                    if spy_bars:
                        market_context["spy_open"] = spy_bars.get("open", 0)
                        market_context["spy_high"] = spy_bars.get("high", 0)
                        market_context["spy_low"] = spy_bars.get("low", 0)
                        market_context["spy_close"] = spy_bars.get("close", 0)
                        market_context["spy_volume"] = spy_bars.get("volume", 0)
                    
                    # Get VIX
                    vix_data = self.polygon.get_vix_level(self.target_date)
                    if vix_data:
                        market_context["vix_level"] = vix_data.get("close")
                    
                    # Get M5 bars for traded tickers
                    m5_summary = {}
                    traded_tickers = set(t.ticker for t in trades)
                    for ticker in traded_tickers:
                        m5_bars = self.polygon.get_m5_bars(ticker, self.target_date)
                        if m5_bars:
                            opening_bars = m5_bars[:6] if len(m5_bars) >= 6 else m5_bars
                            closing_bars = m5_bars[-6:] if len(m5_bars) >= 6 else m5_bars
                            
                            m5_summary[ticker] = {
                                "opening_range": {
                                    "high": max(b.get("high", 0) for b in opening_bars),
                                    "low": min(b.get("low", float("inf")) for b in opening_bars),
                                    "bars": len(opening_bars),
                                },
                                "closing_range": {
                                    "high": max(b.get("high", 0) for b in closing_bars),
                                    "low": min(b.get("low", float("inf")) for b in closing_bars),
                                    "bars": len(closing_bars),
                                },
                                "total_bars": len(m5_bars),
                            }
                    
                    m5_data = {
                        "summary": m5_summary,
                        "note": "Full M5 bar data available - showing opening and closing ranges for AI analysis",
                    }
                except Exception as e:
                    m5_data = {"summary": {}, "note": f"Polygon error: {str(e)}"}
            
            # Assemble complete export
            export_data = {
                "meta": {
                    "date": self.target_date,
                    "generated_at": datetime.now().isoformat(),
                    "epoch_version": "1.1",  # Updated version
                    "tickers_analyzed": len(zones),
                    "ticker_list": sorted(zones.keys()),
                },
                "market_context": market_context,
                "tier_summary": tier_summary,  # V1.1: Added tier summary
                "zone_analysis": zone_analysis,
                "trades": [self._trade_to_dict(t) for t in trades],
                "no_trades": [self._no_trade_to_dict(nt) for nt in no_trades],
                "statistics": statistics,
                "validation_checks": validation,
                # Entry enrichment data (health scores, structure, indicators)
                "entry_analysis": {
                    "total_entries": len(entry_events),
                    "entries": {
                        trade_id: self._entry_event_to_dict(ee)
                        for trade_id, ee in entry_events.items()
                    } if entry_events else {},
                    "health_summary": self._build_health_summary(entry_events) if entry_events else {},
                },
                # Exit event timeline (state changes during trades)
                "exit_events": {
                    "total_events": sum(len(events) for events in exit_events.values()),
                    "trades_with_events": len(exit_events),
                    "events_by_trade": {
                        trade_id: self._exit_events_to_dict(events)
                        for trade_id, events in exit_events.items()
                    } if exit_events else {},
                },
                # Optimal trade analysis (MFE/MAE, capture efficiency)
                "optimal_trade_analysis": {
                    "total_analyzed": len(optimal_trades),
                    "trades": {
                        trade_id: self._optimal_trade_to_dict(ot)
                        for trade_id, ot in optimal_trades.items()
                    } if optimal_trades else {},
                    "efficiency_summary": self._build_efficiency_summary(optimal_trades) if optimal_trades else {},
                },
                "m5_price_data": m5_data,
                "future_indicators": {
                    "vwap": {"status": "planned", "note": "Will include VWAP levels and deviations"},
                    "ema_9": {"status": "planned", "note": "9-period EMA for momentum"},
                    "ema_21": {"status": "planned", "note": "21-period EMA for trend"},
                    "atr_14": {"status": "planned", "note": "14-period ATR for volatility"},
                    "rsi_14": {"status": "planned", "note": "14-period RSI for momentum"},
                    "volume_profile": {"status": "planned", "note": "Intraday volume distribution"},
                },
            }
            
            return export_data
            
        finally:
            self.excel_reader.close()
    
    def save_json(self, output_path: Path = None) -> Path:
        """Export and save to JSON file."""
        data = self.export()
        
        if output_path is None:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            output_path = OUTPUT_DIR / f"epoch_analysis_{self.target_date}.json"
        
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        
        return output_path
    
    def to_clipboard(self) -> str:
        """Export and copy to clipboard."""
        try:
            import pyperclip
            data = self.export()
            json_str = json.dumps(data, indent=2)
            pyperclip.copy(json_str)
            return json_str
        except ImportError:
            print("pyperclip not installed - run: pip install pyperclip")
            return ""


def main():
    """Test the daily exporter."""
    from datetime import date
    
    today = date.today().strftime("%Y-%m-%d")
    print(f"Exporting data for {today} (V1.1 with Tier)...")
    
    exporter = DailyExporter(target_date=today, skip_polygon=True)
    data = exporter.export()
    
    print(f"\nTrades: {len(data['trades'])}")
    print(f"No-trades: {len(data['no_trades'])}")
    print(f"Tickers: {data['meta']['ticker_list']}")
    
    # V1.1: Show tier summary
    tier = data.get('tier_summary', {})
    if tier:
        print(f"\nTier Summary:")
        print(f"  T1 (Premium): {tier.get('by_tier', {}).get('T1', 0)} zones ({tier.get('t1_percentage', 0)}%)")
        print(f"  T2 (Standard): {tier.get('by_tier', {}).get('T2', 0)} zones ({tier.get('t2_percentage', 0)}%)")
        print(f"  T3 (Marginal): {tier.get('by_tier', {}).get('T3', 0)} zones ({tier.get('t3_percentage', 0)}%)")
    
    # Show sample zone with tier
    if data['zone_analysis']:
        ticker = list(data['zone_analysis'].keys())[0]
        zone = data['zone_analysis'][ticker]
        print(f"\nSample zone ({ticker}):")
        if zone.get('primary_zone'):
            pz = zone['primary_zone']
            print(f"  Primary: {pz['zone_high']:.2f}-{pz['zone_low']:.2f}, Tier: {pz['tier']}")
    
    print("\nStatistics:")
    stats = data['statistics']['overall']
    print(f"  Win rate: {stats['win_rate']:.1%}")
    print(f"  Net R: {stats['net_pnl_r']:.2f}")
    
    print(f"\nSPY Direction: {data['market_context']['spy_direction']}")


if __name__ == "__main__":
    main()