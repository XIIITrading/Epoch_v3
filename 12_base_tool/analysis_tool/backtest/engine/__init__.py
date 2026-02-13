"""
EPOCH BACKTESTER v2.0 - Engine Module
"""
from .trade_simulator import TradeSimulator, ActivePosition, CompletedTrade, generate_trade_id

__all__ = ['TradeSimulator', 'ActivePosition', 'CompletedTrade', 'generate_trade_id']