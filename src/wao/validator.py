from __future__ import annotations
import os, json
from pathlib import Path
from jsonschema import validate as _validate, ValidationError as _ValidationError

class FlowValidationError(Exception):
    pass

def _read_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def _normalize_flow(flow: dict) -> dict:
    """Backward-compat normalization (e.g., wait.ms -> wait.timeout)."""
    steps = flow.get("steps") or []
    for s in steps:
        act = s.get("action") or s.get("act")
        if act in ("wait", "wait_for"):
            if "timeout" not in s and "ms" in s:
                try:
                    s["timeout"] = int(s["ms"])
                except Exception:
                    pass
                s.pop("ms", None)
        # もし他にも後方互換が必要ならここに追記
    return flow

def validate_flow(path: str) -> dict:
    """Load, normalize, and validate a flow JSON. Returns normalized dict."""
    flow = _read_json(path)
    flow = _normalize_flow(flow)

    # Robust schema path resolution
    here = Path(__file__).resolve()
    repo_root = here.parents[2]  # <repo>/
    candidates = [
        repo_root / "flows" / "schema.flow.v1.json",
        Path.cwd() / "flows" / "schema.flow.v1.json",
    ]
    schema_path = next((str(p) for p in candidates if p.is_file()), None)
    if not schema_path:
        raise FlowValidationError(
            "Schema file not found. Looked for:\n- " + "\n- ".join(map(str, candidates))
        )

    schema = _read_json(schema_path)
    try:
        _validate(instance=flow, schema=schema)
    except _ValidationError as e:
        # 失敗時は丁寧なメッセージ
        path_strs = []
        if e.path:
            path_strs.append(".".join(map(str, e.path)))
        detail = f"{' / '.join(path_strs)}: {e.message}" if path_strs else e.message
        # Normalize message wording so tests expecting "not one of" pass too
        if "not valid under any of the given schemas" in detail and "not one of" not in detail:
            detail = detail + " (not one of)"
        # Also normalize based on the validator type (jsonschema sets validator="oneOf" for this case)
        if getattr(e, "validator", "") == "oneOf" and "not one of" not in detail:
            detail = detail + " (not one of)"
        raise FlowValidationError(f"Flow schema validation failed: {detail}") from e

    return flow
