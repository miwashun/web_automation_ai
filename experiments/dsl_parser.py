import json
import sys
from pathlib import Path
from typing import Any, Dict, cast

from jsonschema import Draft202012Validator, exceptions


def _load_schema() -> Dict[str, Any]:
    """Load shared flow schema from flows/schema.flow.v1.json (Single Source of Truth)."""
    here = Path(__file__).resolve()
    # repo_root = <repo>/ (assuming experiments/ is directly under repo root)
    repo_root = here.parents[1]
    candidates = [
        repo_root / "flows" / "schema.flow.v1.json",
        Path.cwd() / "flows" / "schema.flow.v1.json",
    ]
    for p in candidates:
        if p.is_file():
            return cast(Dict[str, Any], json.loads(p.read_text(encoding="utf-8")))
    searched = "\n- ".join(map(str, candidates))
    raise FileNotFoundError("Schema file not found. Looked for:\n- " + searched)


def _format_error(e: exceptions.ValidationError) -> str:
    loc = " > ".join(str(p) for p in e.absolute_path) or "(root)"
    need = ""
    if e.validator == "required" and isinstance(e.validator_value, list):
        need = f"  missing: {', '.join(e.validator_value)}"
    return f"[{loc}] {e.message}{need}"


def validate_scenario(data: Dict[str, Any]) -> None:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        msgs = "\n".join(_format_error(e) for e in errors)
        raise ValueError("DSL schema validation failed:\n" + msgs)


def load_and_validate(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    validate_scenario(data)
    return cast(Dict[str, Any], data)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python dsl_parser.py <scenario.json>")
        sys.exit(2)
    try:
        scenario = load_and_validate(sys.argv[1])
        print("OK: DSL is valid.")
        # ここで内部表現へ渡す（例: return scenario）
    except ValueError as ve:
        print(str(ve))
        sys.exit(1)
