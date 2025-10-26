from __future__ import annotations

import hashlib
import json
import random
import re
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)

from . import secrets
from .logging_setup import get_logger

log = get_logger(__name__)


class Runner:
    def __init__(self, dsl: Dict[str, Any]):
        self.dsl = dsl
        self.state: Dict[str, Any] = {}
        self.artifacts_dir = Path("artifacts")
        self.failed_dir = self.artifacts_dir / "failed"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.failed_dir.mkdir(parents=True, exist_ok=True)

        # Downloads directory (for wait_download / verify_file)
        self.downloads_dir = self.artifacts_dir / "downloads"
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

        # Trace (JSONL) output
        self.trace_dir = self.artifacts_dir / "trace"
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.trace_path = self.trace_dir / f"run_{self._timestamp()}.jsonl"

        self._pw: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

        # Determine HTTPS error policy (DSL option > env var)
        # DSL example:
        # {
        #   "version": "...",
        #   "options": { "ignore_https_errors": true },
        #   "steps": [...]
        # }
        _opts = self.dsl.get("options") or {}
        _opt_ignore = _opts.get("ignore_https_errors")
        if _opt_ignore is not None:
            ignore_https_errors = bool(_opt_ignore)
        else:
            # Environment override: WAO_IGNORE_HTTPS_ERRORS=1/true/on
            _env_val = secrets.get("WAO_IGNORE_HTTPS_ERRORS", "0") or "0"
            ignore_https_errors = str(_env_val).strip().lower() in {"1", "true", "on", "yes"}

        # --- Playwright bootstrap (single browser/page reused across steps) ---
        try:
            self._pw = sync_playwright().start()
            # Headless by default; adjust if needed
            self._browser = self._pw.chromium.launch(headless=True)
            # use a context for future trace/download features
            self._context = self._browser.new_context(
                accept_downloads=True,
                ignore_https_errors=ignore_https_errors,
            )
            log.info("Browser context: ignore_https_errors=%s", ignore_https_errors)
            self._page = self._context.new_page()
        except Exception as e:
            log.error("Failed to initialize Playwright: %s", e)
            raise

    def _page_req(self) -> Page:
        """Ensure Playwright page is initialized (helps mypy avoid Optional unions)."""
        if self._page is None:
            raise RuntimeError("Playwright page not initialized")
        return self._page

    def _trace(self, kind: str, payload: Dict[str, Any]) -> None:
        """Append a single JSON record to the run trace (artifacts/trace/*.jsonl)."""
        rec: Dict[str, Any] = {"ts": self._timestamp(), "kind": kind}
        rec.update(payload or {})
        try:
            with self.trace_path.open("a", encoding="utf-8") as w:
                w.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            # tracing must never crash the runner
            pass

    @contextmanager
    def _step_scope(self, idx: int, step: Dict[str, Any]) -> Any:
        """Trace step start/ok/err with timing and page URL when possible."""
        t0 = time.perf_counter()
        self._trace("step_start", {"i": idx, "step": step})
        try:
            yield
            ms = int((time.perf_counter() - t0) * 1000)
            url = ""
            try:
                url = getattr(self._page, "url", "") or ""
            except Exception:
                pass
            self._trace("step_ok", {"i": idx, "ms": ms, "url": url})
        except Exception as e:
            ms = int((time.perf_counter() - t0) * 1000)
            url = ""
            try:
                url = getattr(self._page, "url", "") or ""
            except Exception:
                pass
            self._trace("step_err", {"i": idx, "ms": ms, "url": url, "error": str(e)})
            raise

    def run(self) -> None:  # noqa: C901
        steps: List[Dict[str, Any]] = self.dsl.get("steps", [])
        log.info(
            "Run started: site=%s version=%s",
            self.dsl.get("site", "-"),
            self.dsl.get("version", "-"),
        )
        self._trace(
            "run_start",
            {
                "site": self.dsl.get("site", "-"),
                "version": self.dsl.get("version", "-"),
            },
        )
        # unified run-end status will be emitted once in finally
        run_status = "ok"
        run_error = None
        try:
            for i, step in enumerate(steps, start=1):
                # New DSL uses "act", old one used "action"
                kind = step.get("act") or step.get("action")
                log.info("Step %d: act=%s", i, kind)
                try:
                    with self._step_scope(i, step):
                        # ---- Navigation / open ----
                        if kind in ("open_url", "goto"):
                            url = secrets.resolve(step["url"])
                            log.info("  → goto %s", url)
                            page = self._page_req()
                            page.goto(url)

                        elif kind == "wait_for_selector":
                            selector = step["selector"]
                            timeout = int(step.get("timeout", 10000))
                            state = step.get("state") or "visible"  # "attached" | "detached" | "hidden" | "visible"
                            log.info(
                                "  → wait_for_selector selector=%s state=%s timeout=%d",
                                selector,
                                state,
                                timeout,
                            )
                            page = self._page_req()
                            page.wait_for_selector(selector, state=state, timeout=timeout)

                        elif kind == "wait_for_url":
                            substr = step.get("url_substr") or step.get("contains")
                            timeout = int(step.get("timeout", 10000))
                            if not substr:
                                raise ValueError("wait_for_url requires 'url_substr' (or 'contains')")
                            log.info(
                                "  → wait_for_url contains=%s timeout=%d",
                                substr,
                                timeout,
                            )
                            page = self._page_req()
                            page.wait_for_load_state("load", timeout=timeout)
                            deadline = time.time() + (timeout / 1000.0)
                            while time.time() < deadline:
                                if substr in page.url:
                                    break
                                time.sleep(0.05)
                            else:
                                last = page.url
                                raise TimeoutError(
                                    "URL did not contain " f"'{substr}' within {timeout} ms " f"(last={last})"
                                )

                        # ---- Form fill ----
                        elif kind == "fill":
                            sel = step["selector"]
                            val = secrets.resolve(step.get("value"))
                            mask = bool(step.get("mask", False))
                            # Backward-compat: allow "text" if "value" missing
                            if val is None:
                                val = step.get("text", "")
                            log.info("  → fill %s value=%s", sel, ("***" if mask else val))
                            page = self._page_req()
                            page.fill(sel, str(val))

                        # ---- Click ----
                        elif kind == "click":
                            selector = step.get("selector")
                            log.info("  → click selector=%s", selector)
                            if selector:
                                page = self._page_req()
                                page.click(selector)

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
                                    page = self._page_req()
                                    if target == "selector" and step.get("selector"):
                                        page.locator(step["selector"]).screenshot(path=str(p))
                                    else:
                                        full_page = True if target == "fullpage" else False
                                        page.screenshot(path=str(p), full_page=full_page)
                                    log.info("  → screenshot saved: %s", str(p))
                                except Exception as e:
                                    log.error("  ! screenshot failed: %s", e)

                        # ---- Title assertion ----
                        elif kind == "assert_title":
                            try:
                                page = self._page_req()
                                actual = page.title() or ""
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
                                    failed = actual != expected
                                elif match_mode == "contains":
                                    failed = expected not in actual
                                elif match_mode == "matches":
                                    try:
                                        failed = re.search(expected, actual) is None
                                    except re.error as e:
                                        log.error("assert_title regex error: %s", e)
                                        failed = True
                                else:
                                    log.warning(
                                        "  ! unknown match_mode=%s (fallback equals)",
                                        match_mode,
                                    )
                                    failed = actual != expected
                                if failed:
                                    msg = step.get("message") or (
                                        "assert_title failed: "
                                        f"mode={match_mode} expected='{expected}' "
                                        f"got='{actual}'"
                                    )
                                    log.error("%s", msg)
                            else:
                                # Backward compatibility with old DSL (includes/equals)
                                if includes:
                                    for s in includes:
                                        if s not in actual:
                                            log.error(
                                                "assert_title failed: '%s' not in '%s'",
                                                s,
                                                actual,
                                            )
                                            failed = True
                                if equals is not None and actual != equals:
                                    log.error(
                                        "assert_title failed: expected '%s', got '%s'",
                                        equals,
                                        actual,
                                    )
                                    failed = True

                            if failed:
                                self._save_failure_artifacts(reason="assert_title")
                                sys.exit(1)

                        # ---- Wait for a download and save it ----
                        elif kind == "wait_download":
                            pattern = step.get("pattern")
                            if not pattern:
                                raise ValueError("wait_download requires 'pattern' (regex)")
                            timeout = int(step.get("timeout", 30000))
                            to_dir_val = step.get("to", str(self.downloads_dir))
                            to_dir = Path(secrets.resolve(to_dir_val) if isinstance(to_dir_val, str) else to_dir_val)
                            selector = step.get("selector")

                            to_dir.mkdir(parents=True, exist_ok=True)
                            page = self._page_req()
                            log.info(
                                "  → wait_download pattern=%s timeout=%d to=%s",
                                pattern,
                                timeout,
                                to_dir,
                            )
                            # Expect the download, optionally trigger a click
                            with page.expect_download(timeout=timeout) as dl_info:
                                if selector:
                                    log.info("  → click selector=%s (to trigger download)", selector)
                                    page.click(selector)
                            download = dl_info.value
                            suggested = download.suggested_filename
                            if re.search(pattern, suggested) is None:
                                raise ValueError(
                                    f"Downloaded filename '{suggested}' does not match pattern '{pattern}'"
                                )
                            dest_path = to_dir / suggested
                            download.save_as(str(dest_path))
                            self.state["last_download_path"] = str(dest_path)
                            log.info("  → downloaded: %s", dest_path)

                        # ---- Verify a file's hash ----
                        elif kind == "verify_file":
                            path_val = step.get("path")
                            algo = (step.get("hash") or "").lower()
                            expected = step.get("expected")
                            if not path_val or not algo or not expected:
                                raise ValueError("verify_file requires 'path', 'hash', and 'expected'")
                            file_path = Path(secrets.resolve(path_val) if isinstance(path_val, str) else path_val)
                            if not file_path.is_file():
                                raise FileNotFoundError(f"verify_file: not found: {file_path}")
                            if algo not in {"sha256", "sha1", "md5"}:
                                raise ValueError("verify_file 'hash' must be one of: sha256, sha1, md5")

                            h = hashlib.new(algo)
                            with open(file_path, "rb") as rf:
                                for chunk in iter(lambda: rf.read(8192), b""):
                                    h.update(chunk)
                            actual = h.hexdigest()
                            if actual.lower() != str(expected).lower():
                                msg = f"verify_file failed: {algo} expected={expected} actual={actual} path={file_path}"
                                log.error("%s", msg)
                                self._save_failure_artifacts(reason="verify_file")
                                sys.exit(1)
                            log.info("  → verify_file OK: %s=%s (%s)", algo, actual, file_path)

                        # ---- Download (actual implementation) ----
                        elif kind == "download":
                            # Supports either clicking a selector OR opening a direct URL.
                            # Optional keys:
                            #   - selector: CSS selector to click to trigger download
                            #   - url: direct URL that triggers download
                            #   - path: destination file path (defaults to artifacts/downloads/<suggested>)
                            #   - timeout: ms (default 30000)
                            timeout = int(step.get("timeout", 30000))
                            selector = step.get("selector")
                            url_value = step.get("url")

                            if not selector and not url_value:
                                raise ValueError("download requires either 'selector' or 'url'")

                            # Resolve destination path (if provided), else default to downloads/<suggested_filename>
                            dest_val = step.get("path")
                            page = self._page_req()
                            log.info("  → download start timeout=%d selector=%s url=%s", timeout, selector, url_value)

                            with page.expect_download(timeout=timeout) as dl_info:
                                if selector:
                                    log.info("  → click selector=%s (to trigger download)", selector)
                                    page.click(selector)
                                else:
                                    # Direct URL download (navigate to the file URL)
                                    resolved_url = secrets.resolve(url_value)
                                    log.info("  → open download URL: %s", resolved_url)
                                    page.goto(resolved_url)

                            download = dl_info.value
                            suggested = download.suggested_filename
                            # Decide destination path
                            if dest_val:
                                dest_path = Path(secrets.resolve(dest_val) if isinstance(dest_val, str) else dest_val)
                            else:
                                dest_path = self.downloads_dir / suggested

                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                            download.save_as(str(dest_path))
                            self.state["last_download_path"] = str(dest_path)
                            log.info("  → download saved: %s (suggested=%s)", dest_path, suggested)

                        else:
                            log.warning("  ! unknown act/action: %s (skip)", kind)

                except Exception as e:
                    log.error("Step %d failed: %s", i, e)
                    run_status = "error"
                    run_error = str(e)
                    self._save_failure_artifacts(reason="step")
                    raise

        finally:
            try:
                if self._context is not None:
                    try:
                        self._context.close()
                    except Exception:
                        pass
                if self._browser is not None:
                    self._browser.close()
            finally:
                # write a single run_end record based on aggregated status
                try:
                    payload = {"status": run_status}
                    if run_error:
                        payload["error"] = run_error
                    self._trace("run_end", payload)
                except Exception:
                    pass
                if self._pw is not None:
                    self._pw.stop()

        log.info("Run finished")

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    def _save_failure_artifacts(self, reason: str = "error") -> None:
        try:
            page = self._page
            if page is None:
                return
            ts = self._timestamp()
            png = self.failed_dir / f"failed_{reason}_{ts}.png"
            html = self.failed_dir / f"failed_{reason}_{ts}.html"
            try:
                page.screenshot(path=str(png), full_page=True)
                log.error("Saved failure screenshot: %s", png)
            except Exception:
                pass
            try:
                html_content = page.content()
                html.write_text(html_content, encoding="utf-8")
                log.error("Saved failure HTML: %s", html)
            except Exception:
                pass
        except Exception:
            pass
