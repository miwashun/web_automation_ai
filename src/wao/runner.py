from __future__ import annotations
from typing import Any, Dict, List
from .logging_setup import get_logger

log = get_logger(__name__)

class Runner:
    def __init__(self, dsl: Dict[str, Any]):
        self.dsl = dsl

    def run(self) -> None:
        steps: List[Dict[str, Any]] = self.dsl.get("steps", [])
        log.info("Run started: %s", self.dsl.get("name", "unnamed"))
        for i, step in enumerate(steps, start=1):
            kind = step.get("action")
            log.info("Step %d: action=%s", i, kind)
            # TODO: Playwrightなど実処理の実装
            if kind == "open_url":
                log.info("  → open %s", step.get("url"))
            elif kind == "fill":
                log.info("  → fill selector=%s value=***", step.get("selector"))
            elif kind == "click":
                log.info("  → click selector=%s", step.get("selector"))
            elif kind == "wait":
                log.info("  → wait ms=%s", step.get("ms", 1000))
            elif kind == "download":
                log.info("  → download to path=%s", step.get("path", "./artifacts"))
            else:
                log.warning("  ! unknown action: %s (skip)", kind)
        log.info("Run finished")
