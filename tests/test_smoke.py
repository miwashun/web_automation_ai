import json, subprocess, sys, pathlib

def test_cli_runs():
    root = pathlib.Path(__file__).resolve().parents[1]
    python = sys.executable
    ret = subprocess.run([python, str(root / "app.py"), "--run", str(root / "flows/demo_example.json")])
    assert ret.returncode == 0
