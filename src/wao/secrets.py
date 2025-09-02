from __future__ import annotations
import os
from typing import Optional

def get(key: str, default: Optional[str] = None) -> Optional[str]:
    """環境変数から値を取得（将来はプロバイダ切替に対応予定）"""
    return os.getenv(key, default)
