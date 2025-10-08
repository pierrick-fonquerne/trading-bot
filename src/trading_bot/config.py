"""Application configuration helpers for the trading bot."""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Optional


def _parse_float(value: Optional[str], default: float) -> float:
    if value is None or value.strip() == "":
        return default
    try:
        return float(value)
    except ValueError as exc:  # pragma: no cover - defensive programming
        raise ValueError(f"Impossible de convertir la valeur '{value}' en nombre décimal.") from exc


def _parse_int(value: Optional[str], default: int) -> int:
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError as exc:  # pragma: no cover - defensive programming
        raise ValueError(f"Impossible de convertir la valeur '{value}' en entier.") from exc


def _parse_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "vrai", "yes", "oui", "on"}:
        return True
    if normalized in {"0", "false", "faux", "no", "non", "off"}:
        return False
    raise ValueError(
        "Impossible de convertir la valeur '{value}' en booléen. Utilisez true/false.".format(value=value)
    )


@dataclass
class BotConfig:
    """Dataclass representing runtime configuration for the trading bot."""

    exchange: str = "binance"
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    symbol: str = "BTCUSDT"
    quote_asset: str = "USDT"
    base_asset: str = "BTC"
    trade_quantity: float = 0.001
    poll_interval: float = 5.0
    short_window: int = 5
    long_window: int = 20
    max_history: int = 120
    test_mode: bool = True

    @classmethod
    def from_env(cls) -> "BotConfig":
        """Build configuration from environment variables.

        Supported variables::

            ACTIVE_EXCHANGE
            <EXCHANGE>_API_KEY (e.g. BINANCE_API_KEY)
            <EXCHANGE>_API_SECRET (e.g. BINANCE_API_SECRET)
            <EXCHANGE>_SYMBOL (e.g. BINANCE_SYMBOL)
            <EXCHANGE>_QUOTE_ASSET (e.g. BINANCE_QUOTE_ASSET)
            <EXCHANGE>_BASE_ASSET (e.g. BINANCE_BASE_ASSET)
            <EXCHANGE>_TEST_MODE (e.g. BINANCE_TEST_MODE)
            EXCHANGE_API_KEY (fallback)
            EXCHANGE_API_SECRET (fallback)
            MARKET_SYMBOL (fallback)
            MARKET_QUOTE_ASSET (fallback)
            MARKET_BASE_ASSET (fallback)
            BOT_TRADE_QUANTITY
            BOT_POLL_INTERVAL
            BOT_SHORT_WINDOW
            BOT_LONG_WINDOW
            BOT_MAX_HISTORY
            BOT_TEST_MODE
        """

        exchange_raw = os.getenv("ACTIVE_EXCHANGE") or "binance"
        exchange = exchange_raw.strip().lower() or "binance"
        exchange_prefix = exchange.upper()

        def _get_exchange_value(name: str) -> Optional[str]:
            value = os.getenv(f"{exchange_prefix}_{name}")
            if value is not None and value.strip() != "":
                return value
            if exchange_prefix != "BINANCE":
                legacy_value = os.getenv(f"BINANCE_{name}")
                if legacy_value is not None and legacy_value.strip() != "":
                    return legacy_value
            return None

        symbol = (_get_exchange_value("SYMBOL") or os.getenv("MARKET_SYMBOL") or "BTCUSDT").upper()
        quote_asset = _get_exchange_value("QUOTE_ASSET") or os.getenv("MARKET_QUOTE_ASSET") or "USDT"
        base_asset = _get_exchange_value("BASE_ASSET") or os.getenv("MARKET_BASE_ASSET") or "BTC"

        exchange_test_mode = _get_exchange_value("TEST_MODE")
        if exchange_test_mode is not None:
            test_mode = _parse_bool(exchange_test_mode, True)
        else:
            test_mode = _parse_bool(os.getenv("BOT_TEST_MODE"), True)

        return cls(
            exchange=exchange,
            api_key=_get_exchange_value("API_KEY") or os.getenv("EXCHANGE_API_KEY"),
            api_secret=_get_exchange_value("API_SECRET") or os.getenv("EXCHANGE_API_SECRET"),
            symbol=symbol,
            quote_asset=quote_asset,
            base_asset=base_asset,
            trade_quantity=_parse_float(os.getenv("BOT_TRADE_QUANTITY"), 0.001),
            poll_interval=_parse_float(os.getenv("BOT_POLL_INTERVAL"), 5.0),
            short_window=_parse_int(os.getenv("BOT_SHORT_WINDOW"), 5),
            long_window=_parse_int(os.getenv("BOT_LONG_WINDOW"), 20),
            max_history=_parse_int(os.getenv("BOT_MAX_HISTORY"), 120),
            test_mode=test_mode,
        )

    def require_credentials(self) -> None:
        """Ensure that the API credentials are present when trading is enabled."""

        if not self.api_key or not self.api_secret:
            exchange_label = self.exchange.upper()
            raise ValueError(
                "Les identifiants de la plateforme sont nécessaires pour exécuter des ordres. "
                f"Définissez {exchange_label}_API_KEY et {exchange_label}_API_SECRET (ou EXCHANGE_API_KEY/SECRET) dans votre environnement."
            )

