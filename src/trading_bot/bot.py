"""Core trading bot logic coordinating the client and strategy."""
from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Awaitable, Callable, Deque, List, Optional, Sequence

from .binance_client import BinanceClient
from .config import BotConfig
from .errors import TradingBotError
from .strategy import MovingAverageStrategy, TradeSignal


@dataclass
class Trade:
    """Record of a trade executed (or attempted) by the bot."""

    timestamp: datetime
    side: TradeSignal
    price: float
    quantity: float
    status: str
    order_id: Optional[str] = None


@dataclass
class BotUpdate:
    """Message emitted on each bot iteration."""

    price: Optional[float]
    signal: TradeSignal
    trade: Optional[Trade]
    error: Optional[str] = None


class TradingBot:
    """Trading bot orchestrating a strategy and the exchange client."""

    def __init__(self, client: BinanceClient, strategy: MovingAverageStrategy, config: BotConfig) -> None:
        self._client = client
        self._strategy = strategy
        self._config = config
        self._running = False
        self._prices: Deque[float] = deque(maxlen=max(config.max_history, config.long_window + 5))
        self._trades: List[Trade] = []
        self._lock = asyncio.Lock()

    @property
    def trades(self) -> Sequence[Trade]:
        return tuple(self._trades)

    @property
    def prices(self) -> Sequence[float]:
        return tuple(self._prices)

    @property
    def config(self) -> BotConfig:
        return self._config

    @property
    def client(self) -> BinanceClient:
        return self._client

    @property
    def strategy(self) -> MovingAverageStrategy:
        return self._strategy

    @property
    def is_running(self) -> bool:
        return self._running

    async def fetch_price(self) -> float:
        """Fetch the latest market price and update history."""

        price = await asyncio.to_thread(self._client.get_symbol_price, self._config.symbol)
        self._prices.append(price)
        return price

    async def execute_trade(self, signal: TradeSignal, price: float) -> Trade:
        """Execute a trade according to the signal."""

        order = await asyncio.to_thread(
            self._client.place_market_order,
            self._config.symbol,
            signal.value,
            self._config.trade_quantity,
            test_mode=self._config.test_mode,
        )
        trade = Trade(
            timestamp=datetime.utcnow(),
            side=signal,
            price=price,
            quantity=self._config.trade_quantity,
            status=str(order.get("status", "FILLED")),
            order_id=str(order.get("orderId")) if order.get("orderId") is not None else None,
        )
        self._trades.append(trade)
        return trade

    async def _emit_update(
        self,
        callback: Optional[Callable[[BotUpdate], Awaitable[None]]],
        *,
        price: Optional[float],
        signal: TradeSignal,
        trade: Optional[Trade],
        error: Optional[str] = None,
    ) -> None:
        if callback is not None:
            await callback(BotUpdate(price=price, signal=signal, trade=trade, error=error))

    async def run(self, callback: Optional[Callable[[BotUpdate], Awaitable[None]]] = None) -> None:
        """Start the trading loop until :meth:`stop` is called."""

        async with self._lock:
            if self._running:
                return
            self._running = True

        try:
            while self._running:
                try:
                    price = await self.fetch_price()
                except TradingBotError as exc:
                    await self._emit_update(callback, price=None, signal=TradeSignal.HOLD, trade=None, error=str(exc))
                    await asyncio.sleep(self._config.poll_interval)
                    continue

                signal = self._strategy.evaluate(self._prices)
                trade: Optional[Trade] = None
                error: Optional[str] = None

                if signal in {TradeSignal.BUY, TradeSignal.SELL}:
                    try:
                        trade = await self.execute_trade(signal, price)
                    except TradingBotError as exc:
                        error = str(exc)

                await self._emit_update(callback, price=price, signal=signal, trade=trade, error=error)
                await asyncio.sleep(self._config.poll_interval)
        finally:
            self._running = False

    def stop(self) -> None:
        """Signal the trading loop to stop."""

        self._running = False

