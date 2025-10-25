import os
from pathlib import Path

import pytest

from wao.validator import FlowValidationError, validate_flow

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_valid_flow(tmp_path: Path) -> None:
    flow = {
        "version": "0.1.0",
        "name": "ok",
        "steps": [
            {"action": "open_url", "name": "go", "url": "https://example.com"},
            {"action": "wait", "name": "w", "ms": 100},
        ],
    }
    flow_path = tmp_path / "flow.json"
    flow_path.write_text(__import__("json").dumps(flow), encoding="utf-8")

    result = validate_flow(str(flow_path))
    assert result["name"] == "ok"


def test_invalid_action(tmp_path: Path) -> None:
    flow = {
        "version": "0.1.0",
        "name": "ng",
        "steps": [{"action": "goto", "name": "oops"}],
    }
    flow_path = tmp_path / "flow.json"
    flow_path.write_text(__import__("json").dumps(flow), encoding="utf-8")

    with pytest.raises(FlowValidationError) as ei:
        validate_flow(str(flow_path))
    assert "not one of" in str(ei.value)
