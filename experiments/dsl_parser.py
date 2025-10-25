import json
import sys
from typing import Any, Dict, cast

from jsonschema import Draft202012Validator, exceptions

SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["version", "site", "steps"],
    "properties": {
        "version": {"type": "string"},
        "site": {"type": "string", "minLength": 1},
        "steps": {"type": "array", "items": {"$ref": "#/$defs/Step"}, "minItems": 1},
    },
    "$defs": {
        "Step": {
            "type": "object",
            "required": ["act"],
            "properties": {"act": {"type": "string"}},
            "oneOf": [
                # ---- 基本アクション ----
                {
                    "properties": {"act": {"const": "goto"}, "url": {"type": "string"}},
                    "required": ["url"],
                },
                {
                    "properties": {
                        "act": {"const": "fill"},
                        "selector": {"type": "string"},
                        "text": {"type": "string"},
                        "mask": {"type": "boolean"},
                    },
                    "required": ["selector", "text"],
                },
                {
                    "properties": {
                        "act": {"const": "click"},
                        "selector": {"type": "string"},
                    },
                    "required": ["selector"],
                },
                {
                    "properties": {
                        "act": {"const": "wait"},
                        "for": {"type": "string"},
                        "timeout": {"type": "integer", "minimum": 0},
                    }
                },
                {
                    "properties": {
                        "act": {"const": "wait_for"},
                        "selector": {"type": "string"},
                        "state": {
                            "enum": [
                                "attached",
                                "detached",
                                "visible",
                                "hidden",
                                "enabled",
                                "disabled",
                                "stable",
                            ]
                        },
                        "timeout": {"type": "integer", "minimum": 0},
                    }
                },
                # ---- 成果物/検証（既存） ----
                {
                    "properties": {
                        "act": {"const": "screenshot"},
                        "target": {"enum": ["fullpage", "viewport", "selector"]},
                        "path": {"type": "string"},
                        "record": {"type": "boolean"},
                    }
                },
                {
                    "properties": {
                        "act": {"const": "wait_download"},
                        "pattern": {"type": "string"},
                        "to": {"type": "string"},
                    },
                    "required": ["pattern"],
                },
                {
                    "properties": {
                        "act": {"const": "verify_file"},
                        "hash": {"enum": ["sha256", "sha1", "md5"]},
                        "record": {"type": "boolean"},
                    }
                },
                # ---- 今回追加（log / sleep_random / assert_title） ----
                {
                    "properties": {
                        "act": {"const": "log"},
                        "message": {"type": "string"},
                        "level": {"enum": ["info", "warn", "error"]},
                    },
                    "required": ["message"],
                },
                {
                    "properties": {
                        "act": {"const": "sleep_random"},
                        "min_ms": {"type": "integer", "minimum": 0},
                        "max_ms": {"type": "integer", "minimum": 0},
                    },
                    "required": ["min_ms", "max_ms"],
                },
                {
                    "properties": {
                        "act": {"const": "assert_title"},
                        "expected": {"type": "string"},
                        "match_mode": {"enum": ["equals", "contains", "matches"]},
                        "message": {"type": "string"},
                    },
                    "required": ["expected"],
                },
            ],
        }
    },
}


def _format_error(e: exceptions.ValidationError) -> str:
    loc = " > ".join(str(p) for p in e.absolute_path) or "(root)"
    need = ""
    if e.validator == "required" and isinstance(e.validator_value, list):
        need = f"  missing: {', '.join(e.validator_value)}"
    return f"[{loc}] {e.message}{need}"


def validate_scenario(data: Dict[str, Any]) -> None:
    validator = Draft202012Validator(SCHEMA)
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
