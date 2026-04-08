#!/usr/bin/env bash
# Быстрый деплой на сервере: pull + pip + restart systemd.
# Репозиторий может лежать где угодно (например ~/vpn_tg_bot_template после clone в домашний каталог).
# Один раз: chmod +x scripts/deploy.sh
# Запуск: ./scripts/deploy.sh (из любого места — скрипт сам перейдёт в корень репо)
# Другое имя юнита: SYSTEMD_SERVICE=my-bot.service ./scripts/deploy.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

git pull

if [[ -x venv/bin/pip ]]; then
  venv/bin/pip install -r requirements.txt
elif [[ -f venv/bin/pip ]]; then
  venv/bin/pip install -r requirements.txt
else
  echo "Нет venv/bin/pip — создай окружение: python3 -m venv venv && venv/bin/pip install -r requirements.txt"
  exit 1
fi

SERVICE="${SYSTEMD_SERVICE:-vpn-tg-bot.service}"
sudo systemctl restart "$SERVICE"
sudo systemctl status "$SERVICE" --no-pager -l
