import json
import os

# secrets.json のパスを解決
SECRETS_PATH = os.path.join(os.path.dirname(__file__), "..", "secrets.json")

with open(SECRETS_PATH, encoding="utf-8") as f:
    secrets = json.load(f)

TOKYOGAS_USERNAME = secrets["TOKYOGAS_USERNAME"]
TOKYOGAS_PASSWORD = secrets["TOKYOGAS_PASSWORD"]
