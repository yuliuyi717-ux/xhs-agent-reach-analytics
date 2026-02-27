#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

PY_BIN="${PY_BIN:-python3.11}"

if ! command -v "$PY_BIN" >/dev/null 2>&1; then
  echo "[ERROR] $PY_BIN not found. Please install Python 3.11+"
  exit 1
fi

if [[ ! -d .venv ]]; then
  "$PY_BIN" -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip

# Agent-Reach requires Python 3.10+
python -m pip install "https://github.com/Panniantong/agent-reach/archive/main.zip"
python -m pip install pytest

echo "[DONE] Environment ready."
echo "[NEXT] Activate: source .venv/bin/activate"
echo "[NEXT] Check: agent-reach doctor"
echo "[NEXT] Optional test: python -m pytest -q"