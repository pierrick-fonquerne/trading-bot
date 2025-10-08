"""Entrypoint for running the NiceGUI application."""
from __future__ import annotations

from dotenv import load_dotenv
from nicegui import ui

from trading_bot.nicegui_app import create_app


def main() -> None:
    """Load configuration and start the NiceGUI server."""

    load_dotenv()
    create_app()
    ui.run(title="Atelier de trading automatisé")


if __name__ == "__main__":
    main()

