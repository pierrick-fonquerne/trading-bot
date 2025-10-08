"""Trading strategies and signals."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from statistics import mean
from typing import Sequence


class TradeSignal(Enum):
    """Enumeration of trading signals returned by strategies."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class MovingAverageStrategy:
    """Simple moving average crossover strategy."""

    short_window: int
    long_window: int

    def __post_init__(self) -> None:
        if self.short_window <= 0 or self.long_window <= 0:
            raise ValueError("Les fenêtres de moyenne mobile doivent être positives.")
        if self.short_window >= self.long_window:
            raise ValueError("La fenêtre courte doit être strictement inférieure à la fenêtre longue.")

    def evaluate(self, prices: Sequence[float]) -> TradeSignal:
        """Evaluate the current price history and return a trading signal."""

        if len(prices) < self.long_window + 1:
            return TradeSignal.HOLD

        short_ma = mean(prices[-self.short_window :])
        long_ma = mean(prices[-self.long_window :])
        previous_short = mean(prices[-self.short_window - 1 : -1])
        previous_long = mean(prices[-self.long_window - 1 : -1])

        if short_ma > long_ma and previous_short <= previous_long:
            return TradeSignal.BUY
        if short_ma < long_ma and previous_short >= previous_long:
            return TradeSignal.SELL
        return TradeSignal.HOLD

