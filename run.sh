#!/usr/bin/env bash
# One command to set up and start MARS RETURN. Each step is skipped when already done.
#   ./run.sh              -> http://127.0.0.1:8000
#   PORT=9000 ./run.sh    -> another port
set -euo pipefail
cd "$(dirname "$0")"
PORT="${PORT:-8000}"
PY=.venv/bin/python

python3 -c 'import sys; sys.exit(sys.version_info < (3, 12))' || { echo "Python 3.12 or newer is required." >&2; exit 1; }
command -v npm >/dev/null || { echo "Node.js with npm is required." >&2; exit 1; }

if [ ! -x "$PY" ]; then
  echo "==> Creating Python environment"
  python3 -m venv .venv
fi
if [ ! -f .venv/.installed ] || [ server/requirements.lock -nt .venv/.installed ]; then
  echo "==> Installing Python packages"
  "$PY" -m pip install -q --disable-pip-version-check -r server/requirements.lock
  touch .venv/.installed
fi

if [ ! -f data/region/elevation.json ] || [ ! -f data/region/imagery.webp ]; then
  echo "==> Preparing Jezero terrain (first run downloads ~450 MB from USGS)"
  "$PY" -m scripts.prepare_demo
fi

if [ ! -d web/node_modules ] || [ web/package-lock.json -nt web/node_modules ]; then
  echo "==> Installing web packages"
  (cd web && npm ci --no-audit --no-fund)
fi
if [ ! -f web/dist/index.html ] || [ -n "$(find web/src web/index.html -newer web/dist/index.html -print -quit)" ]; then
  echo "==> Building the planner"
  (cd web && npm run build)
fi

echo "==> MARS RETURN at http://127.0.0.1:$PORT  (API docs: /docs, stop with Ctrl+C)"
exec "$PY" -m uvicorn server.api:app --host 127.0.0.1 --port "$PORT"
