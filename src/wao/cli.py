from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict

from .logging_setup import get_logger
from .runner import Runner
from .validator import FlowValidationError, validate_flow

log = get_logger(__name__)


def main(argv: list[str] | None = None) -> int:
    """Minimal CLI entry: validate a flow JSON then execute with Runner."""
    p = argparse.ArgumentParser(description="Web Automatic Operation CLI")
    p.add_argument("--run", type=Path, help="Path to a flow JSON to execute")
    p.add_argument("--validate", action="store_true", help="Only validate the flow and exit")
    args = p.parse_args(argv)

    if not args.run:
        p.print_help()
        return 2

    try:
        flow: Dict[str, Any] = validate_flow(str(args.run))
    except FlowValidationError as e:
        log.error("%s", str(e))
        return 1

    if args.validate:
        print(f"[OK] Flow is valid: {args.run}")
        return 0

    Runner(flow).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
