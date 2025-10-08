# Trading Bot avec NiceGUI

Ce projet fournit un atelier de trading automatisé construit avec NiceGUI. L'application expose une interface modulaire qui permet de piloter différents produits (crypto, actions, obligations, …) et plateformes (Binance, Coinbase, etc.). Le MVP inclus dans ce dépôt propose un premier module axé sur les cryptomonnaies via Binance, mais l'architecture est conçue pour accueillir d'autres modules au fil du temps.

## Fonctionnalités

- Architecture modulaire : les produits de marché sont organisés par onglets et chaque plateforme est encapsulée dans son propre module.
- Récupération du prix en temps réel pour la paire configurée (par défaut `BTCUSDT`).
- Stratégie de trading basée sur un croisement de moyennes mobiles paramétrable.
- Exécution d'ordres marché en mode test ou réel selon la plateforme.
- Tableau de bord NiceGUI affichant statut du bot, signaux, graphique de prix et journal des trades.
- Chargement de la configuration via des variables d'environnement (support `.env`).

## Prérequis

- Python 3.10 ou supérieur.
- Une paire de clés API pour la plateforme ciblée. Pour le module Binance fourni, vous pouvez créer un compte testnet sur <https://testnet.binance.vision/>.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copiez le fichier `.env.example` vers `.env` et renseignez vos informations d'authentification et de stratégie :

```bash
cp .env.example .env
```

## Configuration

Les variables d'environnement suivantes sont reconnues :

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `ACTIVE_EXCHANGE` | Identifiant du module actif (`binance` dans le MVP) | `binance` |
| `EXCHANGE_API_KEY` | Clé API générique utilisée si aucun champ dédié n'est fourni | — |
| `EXCHANGE_API_SECRET` | Secret API générique | — |
| `MARKET_SYMBOL` | Surcharge générique du symbole (quel que soit le module) | `BTCUSDT` |
| `MARKET_QUOTE_ASSET` | Surcharge générique de l'actif de cotation | `USDT` |
| `MARKET_BASE_ASSET` | Surcharge générique de l'actif de base | `BTC` |
| `BOT_TRADE_QUANTITY` | Quantité échangée par ordre | `0.001` |
| `BOT_POLL_INTERVAL` | Intervalle (en secondes) entre deux évaluations | `5.0` |
| `BOT_SHORT_WINDOW` | Taille de la moyenne mobile courte | `5` |
| `BOT_LONG_WINDOW` | Taille de la moyenne mobile longue | `20` |
| `BOT_MAX_HISTORY` | Nombre maximum de points conservés pour le graphique | `120` |
| `BOT_TEST_MODE` | `true` pour le mode simulation global | `true` |

Chaque plateforme peut définir ses propres variables préfixées. Pour Binance, utilisez les variables suivantes :

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `BINANCE_API_KEY` | Clé API dédiée au module Binance | — |
| `BINANCE_API_SECRET` | Secret API pour Binance | — |
| `BINANCE_SYMBOL` | Paire de trading à suivre | `BTCUSDT` |
| `BINANCE_QUOTE_ASSET` | Actif de cotation pour l'affichage du solde | `USDT` |
| `BINANCE_BASE_ASSET` | Actif de base de la paire | `BTC` |
| `BINANCE_TEST_MODE` | `true` pour utiliser le testnet Binance | `true` |

> ⚠️ **Attention** : pour exécuter de vrais ordres (`BINANCE_TEST_MODE=false` ou `BOT_TEST_MODE=false`), assurez-vous de bien comprendre les risques liés au trading automatisé et d'avoir vérifié votre configuration auprès de la plateforme choisie.

## Lancement de l'application

```bash
python -m src.main
```

L'application NiceGUI démarre un serveur accessible par défaut sur <http://localhost:8080>. Depuis l'interface, utilisez les boutons pour démarrer/arrêter le bot, rafraîchir les soldes et suivre l'activité de chaque module.

## Structure du projet

```
├── requirements.txt
├── README.md
└── src
    ├── main.py
    └── trading_bot
        ├── __init__.py
        ├── binance_client.py          # Module Binance (MVP)
        ├── bot.py
        ├── config.py
        ├── errors.py
        ├── nicegui_app.py
        └── strategy.py
```

## Aller plus loin

- Implémentez vos propres stratégies en créant de nouvelles classes dans `strategy.py`.
- Ajoutez de nouveaux modules (autres courtiers, produits financiers, …) en suivant la même approche que le module Binance.
- Connectez la websocket de la plateforme pour des données de marché plus fréquentes.
- Ajoutez une base de données pour persister l'historique des trades et analyser les performances.

## Licence

Ce projet est distribué sous licence MIT. Voir le fichier [LICENSE](LICENSE).

