# VPN Telegram Bot

A production-oriented Telegram bot for selling and automatically provisioning VPN subscriptions through one or more [3x-ui](https://github.com/MHSanaei/3x-ui) panels.

The service supports trials, paid plans, load distribution across VPN backends, payment webhooks, PostgreSQL persistence, and connection guides for mobile and desktop clients.

> This repository is a technical portfolio project. Configure your own infrastructure, credentials, pricing, branding, and legal requirements before production use.

## Features

### VPN provisioning

- automatic trial and paid subscription creation;
- single-panel and multi-panel 3x-ui configurations;
- weighted least-load backend selection;
- client provisioning across enabled inbounds;
- current and legacy 3x-ui API support;
- subscription URL generation and persistence;
- access reissue and troubleshooting flows;
- configurable trial duration, traffic quota, and IP limit.

### Payments

- RUB payments through WATA H2H;
- USDT payments through Crypto Pay;
- Telegram Stars payments;
- signed WATA and Crypto Pay webhook verification;
- persistent payment order state;
- concurrency-safe provisioning after payment;
- automatic replacement of trial access with paid access;
- extension of active paid subscriptions.

### Telegram experience

- aiogram 3 router-based architecture;
- channel subscription verification middleware;
- inline profile, billing, support, and connection screens;
- guides for iPhone, Android, Windows, and macOS;
- localized Russian UI;
- single-instance polling lock.

### Operations

- async PostgreSQL pool with asyncpg;
- automatic database schema initialization;
- aiohttp payment webhook server;
- systemd service example;
- deployment helper;
- password-safe database logging.

## Architecture

~~~mermaid
flowchart LR
    U[Telegram user] --> TG[Telegram Bot API]
    TG --> B[aiogram bot]
    B --> DB[(PostgreSQL)]
    B --> REG[3x-ui backend registry]
    REG --> P1[3x-ui panel A]
    REG --> P2[3x-ui panel B]
    REG --> PN[3x-ui panel N]
    B --> W[WATA H2H]
    B --> C[Crypto Pay]
    B --> S[Telegram Stars]
    W --> H[aiohttp webhook server]
    C --> H
    H --> DB
    H --> PROV[Access provisioning]
    PROV --> REG
    PROV --> TG
~~~

A successful payment is stored before provisioning. The service claims the order, chooses a backend, creates the VPN client, persists subscription data, and notifies the user.

## Technology stack

| Area | Technologies |
| --- | --- |
| Runtime | Python 3.11+ |
| Telegram | aiogram 3 |
| Database | PostgreSQL, asyncpg |
| HTTP | httpx, aiohttp |
| Configuration | Pydantic Settings, python-dotenv |
| VPN control plane | 3x-ui API |
| Payments | WATA H2H, Crypto Pay, Telegram Stars |
| Deployment | Linux, systemd, Bash |

## Repository structure

~~~text
.
+-- app/
|   +-- handlers/          # Telegram commands and callbacks
|   +-- keyboards/         # Inline keyboards
|   +-- middlewares/       # Subscription and 3x-ui middleware
|   +-- services/          # Billing, provisioning, and UI flows
|   +-- config.py          # Environment and backend settings
|   +-- db.py              # asyncpg pool and schema
|   +-- main.py            # Application lifecycle
|   +-- threexui_client.py # 3x-ui API client
|   +-- wata_http.py       # Payment webhook server
+-- assets/                # Telegram UI and guide images
+-- scripts/
|   +-- create_database.py
|   +-- deploy.sh
|   +-- vpn-tg-bot.service.example
+-- .env.example
+-- main.py
+-- requirements.txt
~~~

## Provisioning flow

1. A user activates a trial or selects a paid plan.
2. The bot creates a persistent payment order.
3. WATA, Crypto Pay, or Telegram confirms payment.
4. The order is atomically claimed for provisioning.
5. The registry selects the least-loaded panel, adjusted by weight.
6. A VPN client is created across the target inbounds.
7. The subscription URL, backend key, UUID, and expiration are stored.
8. Replaced trial or paid clients are removed.
9. The user receives the subscription and platform instructions.

## Quick start

### Requirements

- Python 3.11+
- PostgreSQL
- a Telegram bot token from [@BotFather](https://t.me/BotFather)
- a running 3x-ui panel
- a Telegram channel for subscription verification

### Install

~~~bash
git clone https://github.com/nGrUnD/vpn_tg_bot_template.git
cd vpn_tg_bot_template

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
~~~

Windows activation:

~~~powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
~~~

### Minimal configuration

~~~dotenv
BOT_TOKEN=replace-with-your-telegram-bot-token
DATABASE_URL=postgresql://vpn_bot:strong-password@localhost:5432/vpn_bot

CHANNEL_USERNAME=@your_channel
CHANNEL_URL=https://t.me/your_channel

TRIAL_DAYS=3
TRIAL_TRAFFIC_GB=0

THREEXUI_BASE_URL=https://panel.example.com
THREEXUI_USERNAME=panel-user
THREEXUI_PASSWORD=strong-panel-password
THREEXUI_VLESS_SERVER=vpn.example.com
THREEXUI_VLESS_PORT=443
THREEXUI_INBOUND_ID=1
~~~

Multiple panels can be configured through **THREEXUI_BACKENDS_JSON**:

~~~dotenv
THREEXUI_BACKENDS_JSON=[{"key":"nl","base_url":"https://nl.example.com","username":"admin","password":"secret","weight":1},{"key":"de","base_url":"https://de.example.com","username":"admin","password":"secret","weight":2}]
THREEXUI_DEFAULT_KEY=nl
~~~

### Prepare PostgreSQL

Create the database manually or use the helper:

~~~bash
export PG_SUPER_DSN='postgresql://postgres:superuser-password@localhost:5432/postgres'
export VPN_BOT_DB_NAME='vpn_bot'
export VPN_BOT_DB_USER='vpn_bot'
export VPN_BOT_DB_PASSWORD='strong-password'
python scripts/create_database.py
~~~

Tables are created and updated automatically during application startup.

### Run

~~~bash
python main.py
~~~

Alternative entry point:

~~~bash
python -m app
~~~

Only one polling process may use a bot token. A local lock protects against duplicate processes on one host.

## Payment configuration

All payment integrations are optional.

### WATA H2H

~~~dotenv
WATA_ACCESS_TOKEN=merchant-access-token
WATA_API_BASE=https://api.wata.pro/api/h2h
HTTP_WEBHOOK_HOST=0.0.0.0
HTTP_WEBHOOK_PORT=8080
WATA_WEBHOOK_PATH=/webhooks/wata
WATA_WEBHOOK_VERIFY_SIGNATURE=true
~~~

### Crypto Pay

~~~dotenv
CRYPTOPAY_API_TOKEN=crypto-pay-token
CRYPTOPAY_TESTNET=false
CRYPTOPAY_RUB_PER_USDT=83
HTTP_WEBHOOK_HOST=0.0.0.0
HTTP_WEBHOOK_PORT=8080
CRYPTOPAY_WEBHOOK_PATH=/webhooks/cryptobot
CRYPTOPAY_WEBHOOK_VERIFY_SIGNATURE=true
CRYPTOPAY_WEBHOOK_PUBLIC_URL=https://bot.example.com/webhooks/cryptobot
~~~

Configure public HTTPS webhook URLs in the provider dashboards. Telegram Stars invoices work through the Telegram Bot API without an external provider token.

## Deployment

Expose the internal webhook server through an HTTPS reverse proxy:

~~~text
Internet -> HTTPS reverse proxy -> 127.0.0.1:8080
~~~

Install the systemd unit after adjusting its user and paths:

~~~bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
sudo cp scripts/vpn-tg-bot.service.example /etc/systemd/system/vpn-tg-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now vpn-tg-bot.service
~~~

Deploy later updates with:

~~~bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
~~~

## Security

- never commit .env, bot tokens, database passwords, payment tokens, or panel credentials;
- use HTTPS for webhooks and 3x-ui panels;
- keep WATA and Crypto Pay signature verification enabled;
- place PostgreSQL and webhook ports behind a firewall;
- use a least-privileged PostgreSQL role;
- rotate credentials that were ever shared publicly;
- keep one Telegram poller active per bot token.

## Author

**Semen Teneshev** - Python Backend Developer

GitHub: [@nGrUnD](https://github.com/nGrUnD)