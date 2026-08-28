#!/usr/bin/env bash
set -euo pipefail
# Install the Python runtime used by the Discord gateway and backend modules.
python3 -m pip install --user --disable-pip-version-check -q -r requirements-bot.txt
if [[ -n "${DISCORD_BOT_TOKEN:-}" ]]; then
  python3 bot.py &
  BOT_PID=$!
  trap 'kill "$BOT_PID" 2>/dev/null || true' EXIT TERM INT
else
  echo "DISCORD_BOT_TOKEN not set; starting dashboard/API only"
fi
exec node dist/server.cjs
