from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from jsonschema import validate, ValidationError
from .runner import Runner
from .logging_setup import get_logger

log = get_logger(__name__)

def _load_schema() -> dict:
    here = Path(__file__).resolve().parent
    with open(here / "schema.json", "r", encoding="utf-8") as f:
        return json.load(f)

def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Web Automatic Operation CLI (skeleton)")
    p.add_argument("--run", type=Path, help="DSL JSON を実行")
    args = p.parse_args(argv)

    if not args.run:
        p.print_help()
        return 2

    schema = _load_schema()
    dsl = _load_json(args.run)

    try:
        validate(instance=dsl, schema=schema)
    except ValidationError as e:
        log.error("DSL validation error: %s", e.message)
        return 1

    Runner(dsl).run()
    return 0
