"""Wrapper around the Binance REST API using binance-connector."""
from __future__ import annotations

from typing import Any, Dict, Optional
import time

from .errors import TradingBotError

try:  # pragma: no cover - import is environment dependent
    from binance.error import ClientError  # type: ignore
    from binance.spot import Spot as BinanceSpot  # type: ignore
except ImportError:  # pragma: no cover - handled at runtime
    BinanceSpot = None  # type: ignore
    ClientError = Exception  # type: ignore


class BinanceClient:
    """Thin wrapper around the Binance Spot REST client."""

    def __init__(self, api_key: Optional[str], api_secret: Optional[str], *, testnet: bool = False) -> None:
        if BinanceSpot is None:
            raise TradingBotError(
                "Le package 'binance-connector' est requis. Installez-le avec 'pip install binance-connector'."
            )
        base_url = "https://testnet.binance.vision" if testnet else None
        self._client = BinanceSpot(api_key=api_key, api_secret=api_secret, base_url=base_url)
        self._testnet = testnet

    @property
    def is_testnet(self) -> bool:
        return self._testnet

    def get_symbol_price(self, symbol: str) -> float:
        """Return the latest ticker price for the provided symbol."""

        try:
            ticker: Dict[str, Any] = self._client.ticker_price(symbol=symbol)
        except ClientError as exc:  # pragma: no cover - requires live API
            raise TradingBotError(f"Impossible de récupérer le prix pour {symbol}: {exc}") from exc
        price = ticker.get("price")
        if price is None:
            raise TradingBotError(f"Réponse inattendue de Binance pour le symbole {symbol}: {ticker}")
        return float(price)

    def get_account_balance(self, asset: str) -> float:
        """Retrieve the free balance for a given asset."""

        try:
            account: Dict[str, Any] = self._client.account()
        except ClientError as exc:  # pragma: no cover - requires live API
            raise TradingBotError(f"Impossible de récupérer le solde du compte: {exc}") from exc

        for balance in account.get("balances", []):
            if balance.get("asset") == asset:
                return float(balance.get("free", 0))
        return 0.0

    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        *,
        quote_order_qty: Optional[float] = None,
        test_mode: bool = True,
    ) -> Dict[str, Any]:
        """Place a MARKET order on Binance.

        When ``test_mode`` is ``True`` the request uses ``new_order_test`` so no
        real trade will be executed. When ``False`` the order is sent with
        ``new_order`` and may execute immediately depending on market conditions.
        """

        if not self._client.api_key or not self._client.api_secret:
            raise TradingBotError(
                "Les identifiants Binance sont requis pour exécuter un ordre. "
                "Définissez BINANCE_API_KEY et BINANCE_API_SECRET (ou EXCHANGE_API_KEY/SECRET)."
            )

        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
        }
        if quote_order_qty is not None:
            params["quoteOrderQty"] = str(quote_order_qty)
        else:
            params["quantity"] = str(quantity)

        try:
            if test_mode:
                self._client.new_order_test(**params)
                return {
                    "symbol": symbol,
                    "side": side,
                    "status": "TEST",
                    "executedQty": params.get("quantity") or params.get("quoteOrderQty"),
                    "transactTime": int(time.time() * 1000),
                }
            return self._client.new_order(**params)
        except ClientError as exc:  # pragma: no cover - requires live API
            raise TradingBotError(f"Erreur lors de l'exécution de l'ordre: {exc}") from exc

