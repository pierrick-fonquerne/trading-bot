"""NiceGUI interface for the modular trading bot."""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

from nicegui import app, ui

from .binance_client import BinanceClient
from .bot import BotUpdate, TradingBot
from .config import BotConfig
from .errors import TradingBotError
from .strategy import MovingAverageStrategy, TradeSignal


def create_app(config: Optional[BotConfig] = None) -> TradingBot:
    """Configure the NiceGUI interface and return the bot instance."""

    cfg = config or BotConfig.from_env()
    strategy = MovingAverageStrategy(cfg.short_window, cfg.long_window)
    client = BinanceClient(cfg.api_key, cfg.api_secret, testnet=cfg.test_mode)
    bot = TradingBot(client=client, strategy=strategy, config=cfg)

    ui.page_title("Atelier de trading automatisé")
    ui.markdown(
        """# Atelier de trading automatisé\n"
        "Une interface modulaire pour piloter des robots de trading. Sélectionnez votre produit,"
        " puis activez le module correspondant pour gérer vos stratégies."""
    )

    with ui.tabs().classes("w-full mt-4") as tabs:
        crypto_tab = ui.tab("Crypto-monnaies", icon="currency_bitcoin")

    tabs.value = crypto_tab

    with ui.tab_panels(tabs, value=crypto_tab).classes("w-full"):
        with ui.tab_panel(crypto_tab):
            ui.markdown(
                """## Crypto-monnaies\n"
                "Le MVP se concentre sur un module Binance. D'autres plateformes et produits"
                " pourront être ajoutés ultérieurement à partir de cette même structure."""
            )

            with ui.card().classes("w-full mt-2"):
                with ui.card_section():
                    with ui.row().classes("items-center w-full"):
                        ui.icon("currency_exchange").classes("text-2xl text-primary")
                        ui.label("Module Binance (Crypto)").classes("text-xl font-semibold ml-2")
                        ui.space()
                        ui.badge("Actif").props("color=primary")
                    ui.markdown(
                        "Pilotez vos stratégies crypto via Binance. Cette carte regroupe les indicateurs,"
                        " le suivi des ordres et les actions de contrôle pour le bot."
                    ).classes("text-sm text-gray-600")

                with ui.card_section():
                    with ui.row().classes("items-center gap-4"):
                        status_label = ui.label("Statut: arrêté").classes("text-lg font-medium")
                        price_label = ui.label("Prix actuel: --").classes("text-lg font-mono")
                        signal_label = ui.label("Signal: HOLD").classes("text-lg font-medium")
                    balance_label = ui.label("").classes("text-sm text-gray-600")

                with ui.card_section():
                    chart = ui.echart(
                        {
                            "xAxis": {"type": "category", "data": []},
                            "yAxis": {"type": "value"},
                            "tooltip": {"trigger": "axis"},
                            "series": [
                                {
                                    "name": "Prix",
                                    "type": "line",
                                    "smooth": True,
                                    "showSymbol": False,
                                    "data": [],
                                }
                            ],
                        }
                    ).classes("w-full h-64")

                with ui.card_section():
                    log = ui.log(max_lines=200).classes("w-full")

                with ui.card_section():
                    with ui.row().classes("gap-2"):
                        start_button = ui.button("Démarrer").props("color=positive")
                        stop_button = ui.button("Arrêter").props("color=negative")
                        refresh_button = ui.button("Actualiser le solde")

                with ui.card_section():
                    with ui.expansion("Configuration", icon="settings").classes("w-full"):
                        ui.label(f"Plateforme active: {cfg.exchange.capitalize()}")
                        ui.label(f"Symbole: {cfg.symbol}")
                        ui.label(f"Mode testnet: {'Oui' if cfg.test_mode else 'Non'}")
                        ui.label(f"Fenêtre courte: {cfg.short_window}")
                        ui.label(f"Fenêtre longue: {cfg.long_window}")
                        ui.label(f"Quantité par trade: {cfg.trade_quantity}")
                        ui.label(f"Intervalle de rafraîchissement: {cfg.poll_interval}s")

    timestamps: list[str] = []
    prices: list[float] = []
    bot_task: Optional[asyncio.Task[None]] = None

    async def refresh_balance() -> None:
        if not cfg.api_key or not cfg.api_secret:
            exchange_label = cfg.exchange.upper()
            balance_label.text = (
                "Solde indisponible: configurez "
                f"{exchange_label}_API_KEY et {exchange_label}_API_SECRET (ou EXCHANGE_API_KEY/SECRET) pour l'afficher."
            )
            return
        try:
            balance = await asyncio.to_thread(client.get_account_balance, cfg.quote_asset)
            balance_label.text = f"Solde disponible {cfg.quote_asset}: {balance:.4f}"
        except TradingBotError as exc:
            balance_label.text = f"Solde indisponible: {exc}"

    async def handle_update(update: BotUpdate) -> None:
        if update.price is not None:
            price_label.text = f"Prix actuel ({cfg.symbol}): {update.price:.2f}"
            timestamps.append(datetime.now().strftime("%H:%M:%S"))
            prices.append(round(update.price, 2))
            if len(timestamps) > cfg.max_history:
                timestamps.pop(0)
                prices.pop(0)
            chart.options["xAxis"]["data"] = timestamps
            chart.options["series"][0]["data"] = prices
            chart.update()
        signal_label.text = f"Signal: {update.signal.value}"
        if update.signal is TradeSignal.BUY:
            signal_label.classes(replace="text-lg font-medium text-green-600")
        elif update.signal is TradeSignal.SELL:
            signal_label.classes(replace="text-lg font-medium text-red-600")
        else:
            signal_label.classes(replace="text-lg font-medium")
        if update.trade:
            trade = update.trade
            log.push(
                f"{trade.timestamp:%H:%M:%S} - {trade.side.value} {trade.quantity} @ {trade.price:.2f} ({trade.status})"
            )
        if update.error:
            log.push(f"⚠️ {update.error}")
        status_label.text = "Statut: en cours" if bot.is_running else "Statut: arrêté"

    async def start_bot() -> None:
        nonlocal bot_task
        if bot.is_running:
            status_label.text = "Statut: déjà en cours"
            return
        status_label.text = "Statut: démarrage..."
        await refresh_balance()
        bot_task = asyncio.create_task(bot.run(handle_update))

    async def stop_bot() -> None:
        nonlocal bot_task
        if not bot.is_running:
            status_label.text = "Statut: arrêté"
            return
        bot.stop()
        if bot_task:
            await bot_task
            bot_task = None
        status_label.text = "Statut: arrêté"

    start_button.on("click", start_bot)
    stop_button.on("click", stop_bot)
    refresh_button.on("click", refresh_balance)

    @app.on_shutdown
    async def _shutdown() -> None:
        bot.stop()
        if bot_task:
            await bot_task

    return bot

