#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR=".venv"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "[ERROR] Python not found: $PYTHON_BIN"
  exit 1
fi

"$PYTHON_BIN" -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r requirements.txt

if [[ ! -f profiles.txt && -f profiles.txt.example ]]; then
  cp profiles.txt.example profiles.txt
fi

echo "[OK] Installation complete"
echo "Activate env: source .venv/bin/activate"
echo "Run app: python app.py"
