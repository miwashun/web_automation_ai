#!/usr/bin/env bash
set -euo pipefail

# プロジェクトの .venv があれば優先
if [[ -f ".venv/bin/python" ]]; then
  PY=".venv/bin/python"
else
  PY="python"
fi

# pytest が無ければ dev 依存を入れる（初回のみ）
if ! "$PY" -c "import pytest" 2>/dev/null; then
  if [[ -f "requirements-dev.txt" ]]; then
    "$PY" -m pip install -r requirements-dev.txt
  else
    "$PY" -m pip install pytest>=8.0
  fi
fi

exec "$PY" -m pytest -q -vv
