"""Trading bot package exposing a modular NiceGUI interface."""

from .bot import BotUpdate, Trade, TradingBot
from .config import BotConfig
from .strategy import MovingAverageStrategy, TradeSignal

__all__ = [
    "BotConfig",
    "BotUpdate",
    "MovingAverageStrategy",
    "Trade",
    "TradeSignal",
    "TradingBot",
]

