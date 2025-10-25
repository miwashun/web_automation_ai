from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from dotenv import load_dotenv

# --- .env auto-load ---
_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[2] if len(_HERE.parents) >= 2 else Path.cwd()
_DOTENV_CANDIDATES = [
    _REPO_ROOT / ".env",
    Path.cwd() / ".env",
]
for _p in _DOTENV_CANDIDATES:
    if _p.is_file():
        load_dotenv(dotenv_path=_p, override=False)

_ENV_PATTERN = re.compile(r"\$\{ENV:([A-Za-z_][A-Za-z0-9_]*)\}")


def get(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


def _resolve_str(s: str) -> str:
    def _sub(m: re.Match[str]) -> str:
        k = m.group(1)
        return os.environ.get(k, "")

    return _ENV_PATTERN.sub(_sub, s)


def resolve(value: Any) -> Any:
    if isinstance(value, str):
        return _resolve_str(value)
    if isinstance(value, Mapping):
        return {k: resolve(v) for k, v in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [resolve(v) for v in value]
    return value
