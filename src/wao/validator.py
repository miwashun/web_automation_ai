import json
import os
from jsonschema import Draft7Validator, ValidationError

class FlowValidationError(Exception):
    pass

def _read_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def _repo_root_from(path: str) -> str:
    # flows/xxx.json からリポジトリルートを推測（2階層上）
    return os.path.abspath(os.path.join(os.path.dirname(path), ".."))

def validate_flow(flow_path: str, schema_path: str | None = None) -> dict:
    """Flow JSON をスキーマで検証し、辞書を返す。失敗時は FlowValidationError を投げる。"""
    flow_abs = os.path.abspath(flow_path)
    flow = _read_json(flow_abs)

    if schema_path is None:
        repo_root = _repo_root_from(flow_abs)
        schema_path = os.path.join(repo_root, "flows", "schema.flow.v1.json")

    schema = _read_json(schema_path)

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(flow), key=lambda e: e.path)

    if errors:
        lines = []
        for e in errors:
            # 例: steps[1].action: 'goto' is not one of [...]
            loc = "root" if not e.path else "steps" if list(e.path)[0] == "steps" else ".".join(map(str, e.path))
            # もう少し詳細なパス表現
            if e.path:
                parts = []
                for p in e.path:
                    if isinstance(p, int):
                        parts.append(f"[{p}]")
                    else:
                        # 先頭以外はドットで繋ぐ
                        if parts:
                            parts.append(f".{p}")
                        else:
                            parts.append(f"{p}")
                loc = "".join(parts)
            lines.append(f"- {loc}: {e.message}")
        msg = "Flow schema validation failed:\n" + "\n".join(lines)
        raise FlowValidationError(msg)

    return flow
