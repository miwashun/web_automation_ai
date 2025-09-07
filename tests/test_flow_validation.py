import os
import pytest
from wao.validator import validate_flow, FlowValidationError

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

def test_valid_flow(tmp_path):
    flow = {
        "version": "0.1.0",
        "name": "ok",
        "steps": [
            {"action": "open_url", "name": "go", "url": "https://example.com"},
            {"action": "wait", "name": "w", "ms": 100}
        ]
    }
    flow_path = tmp_path / "flow.json"
    flow_path.write_text(__import__("json").dumps(flow), encoding="utf-8")

    # プロジェクトの実スキーマを使う
    # （テスト時は cwd をリポジトリルートにして実行してください）
    result = validate_flow(str(flow_path))
    assert result["name"] == "ok"

def test_invalid_action(tmp_path):
    flow = {
        "version": "0.1.0",
        "name": "ng",
        "steps": [{"action": "goto", "name": "oops"}]
    }
    flow_path = tmp_path / "flow.json"
    flow_path.write_text(__import__("json").dumps(flow), encoding="utf-8")

    with pytest.raises(FlowValidationError) as ei:
        validate_flow(str(flow_path))
    assert "not one of" in str(ei.value)
