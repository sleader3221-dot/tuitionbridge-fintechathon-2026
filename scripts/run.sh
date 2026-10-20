#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
. .venv/bin/activate
exec uvicorn app.asgi:app --host 127.0.0.1 --port "${PORT:-8000}"
