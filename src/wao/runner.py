from __future__ import annotations
from typing import Any, Dict, List
from .logging_setup import get_logger
import time, random, sys, re
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright
from . import secrets

log = get_logger(__name__)

class Runner:
    def __init__(self, dsl: Dict[str, Any]):
        self.dsl = dsl
        self.state: Dict[str, Any] = {}
        self.artifacts_dir = Path("artifacts")
        self.failed_dir = self.artifacts_dir / "failed"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.failed_dir.mkdir(parents=True, exist_ok=True)
        self._pw = None
        self._browser = None
        self._page = None

        # --- Playwright bootstrap (single browser/page reused across steps) ---
        try:
            self._pw = sync_playwright().start()
            # Headless by default; adjust if needed
            self._browser = self._pw.chromium.launch(headless=True)
            self._page = self._browser.new_page()
        except Exception as e:
            log.error("Failed to initialize Playwright: %s", e)
            raise

    def run(self) -> None:
        steps: List[Dict[str, Any]] = self.dsl.get("steps", [])
        log.info("Run started: site=%s version=%s", self.dsl.get("site", "-"), self.dsl.get("version", "-"))
        try:
            for i, step in enumerate(steps, start=1):
                # New DSL uses "act", old one used "action"
                kind = step.get("act") or step.get("action")
                log.info("Step %d: act=%s", i, kind)
                try:

                    # ---- Navigation / open ----
                    if kind in ("open_url", "goto"):
                        url = secrets.resolve(step["url"])
                        log.info("  → goto %s", url)
                        self._page.goto(url)

                    elif kind == "wait_for_selector":
                        selector = step["selector"]
                        timeout = int(step.get("timeout", 10000))
                        state = step.get("state") or "visible"  # "attached" | "detached" | "hidden" | "visible"
                        log.info("  → wait_for_selector selector=%s state=%s timeout=%d", selector, state, timeout)
                        self._page.wait_for_selector(selector, state=state, timeout=timeout)

                    elif kind == "wait_for_url":
                        substr = step.get("url_substr") or step.get("contains")
                        timeout = int(step.get("timeout", 10000))
                        if not substr:
                            raise ValueError("wait_for_url requires 'url_substr' (or 'contains')")
                        log.info("  → wait_for_url contains=%s timeout=%d", substr, timeout)
                        self._page.wait_for_load_state("load", timeout=timeout)
                        deadline = time.time() + (timeout / 1000.0)
                        while time.time() < deadline:
                            if substr in self._page.url:
                                break
                            time.sleep(0.05)
                        else:
                            raise TimeoutError(f"URL did not contain '{substr}' within {timeout} ms (last={self._page.url})")

                    # ---- Form fill ----
                    elif kind == "fill":
                        sel = step["selector"]
                        val = secrets.resolve(step.get("value"))
                        mask = bool(step.get("mask", False))
                        # Backward-compat: allow "text" if "value" missing
                        if val is None:
                            val = step.get("text", "")
                        log.info("  → fill %s value=%s", sel, ("***" if mask else val))
                        self._page.fill(sel, str(val))

                    # ---- Click ----
                    elif kind == "click":
                        selector = step.get("selector")
                        log.info("  → click selector=%s", selector)
                        if selector:
                            self._page.click(selector)

                    # ---- Waits (basic stub) ----
                    elif kind in ("wait", "wait_for"):
                        timeout = int(step.get("timeout", 1000))
                        log.info("  → %s timeout=%d ms", kind, timeout)
                        time.sleep(timeout / 1000.0)

                    # ---- Log ----
                    elif kind == "log":
                        level = step.get("level", "info")
                        msg = step.get("message", "")
                        if level == "warn":
                            log.warning("%s", msg)
                        elif level == "error":
                            log.error("%s", msg)
                        else:
                            log.info("%s", msg)

                    # ---- Random sleep ----
                    elif kind == "sleep_random":
                        min_ms = int(step.get("min_ms", 0))
                        max_ms = int(step.get("max_ms", min_ms))
                        if max_ms < min_ms:
                            min_ms, max_ms = max_ms, min_ms
                        dur = random.randint(min_ms, max_ms)
                        log.info("  → sleep_random %d ms", dur)
                        time.sleep(dur / 1000.0)

                    # ---- Screenshot (stub artifact) ----
                    elif kind == "screenshot":
                        target = step.get("target", "viewport")  # fullpage | viewport | selector
                        path = step.get("path")
                        if not path:
                            log.warning("  ! screenshot skipped: path is required")
                        else:
                            p = Path(path)
                            p.parent.mkdir(parents=True, exist_ok=True)
                            try:
                                if target == "selector" and step.get("selector"):
                                    self._page.locator(step["selector"]).screenshot(path=str(p))
                                else:
                                    full_page = True if target == "fullpage" else False
                                    self._page.screenshot(path=str(p), full_page=full_page)
                                log.info("  → screenshot saved: %s", str(p))
                            except Exception as e:
                                log.error("  ! screenshot failed: %s", e)

                    # ---- Title assertion ----
                    elif kind == "assert_title":
                        try:
                            actual = self._page.title() or ""
                        except Exception:
                            actual = self.state.get("title", "")
                        expected = step.get("expected")
                        match_mode = step.get("match_mode", "equals")
                        includes = step.get("includes")
                        equals = step.get("equals")
                        log.info("  → assert_title against: %s", actual)

                        failed = False
                        if expected is not None:
                            if match_mode == "equals":
                                failed = (actual != expected)
                            elif match_mode == "contains":
                                failed = (expected not in actual)
                            elif match_mode == "matches":
                                try:
                                    failed = (re.search(expected, actual) is None)
                                except re.error as e:
                                    log.error("assert_title regex error: %s", e)
                                    failed = True
                            else:
                                log.warning("  ! unknown match_mode=%s (fallback equals)", match_mode)
                                failed = (actual != expected)
                            if failed:
                                msg = step.get("message") or f"assert_title failed: mode={match_mode} expected='{expected}' got='{actual}'"
                                log.error("%s", msg)
                        else:
                            # Backward compatibility with old DSL (includes/equals)
                            if includes:
                                for s in includes:
                                    if s not in actual:
                                        log.error("assert_title failed: '%s' not in '%s'", s, actual)
                                        failed = True
                            if equals is not None and actual != equals:
                                log.error("assert_title failed: expected '%s', got '%s'", equals, actual)
                                failed = True

                        if failed:
                            self._save_failure_artifacts(reason="assert_title")
                            sys.exit(1)

                    # ---- Download (placeholder) ----
                    elif kind == "download":
                        log.info("  → download to path=%s", step.get("path", "./artifacts"))

                    else:
                        log.warning("  ! unknown act/action: %s (skip)", kind)

                except Exception as e:
                    log.error("Step %d failed: %s", i, e)
                    self._save_failure_artifacts(reason="step")
                    raise

        finally:
            try:
                if self._browser is not None:
                    self._browser.close()
            finally:
                if self._pw is not None:
                    self._pw.stop()

        log.info("Run finished")

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    def _save_failure_artifacts(self, reason: str = "error") -> None:
        try:
            if getattr(self, "_page", None) is None:
                return
            ts = self._timestamp()
            png = self.failed_dir / f"failed_{reason}_{ts}.png"
            html = self.failed_dir / f"failed_{reason}_{ts}.html"
            try:
                self._page.screenshot(path=str(png), full_page=True)
                log.error("Saved failure screenshot: %s", png)
            except Exception:
                pass
            try:
                html_content = self._page.content()
                html.write_text(html_content, encoding="utf-8")
                log.error("Saved failure HTML: %s", html)
            except Exception:
                pass
        except Exception:
            pass
