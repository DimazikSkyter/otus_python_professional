import json
from pathlib import Path

SECRETS_PATH = Path(__file__).resolve().parent.parent / "secrets.json"

with open(SECRETS_PATH) as f:
    secrets = json.load(f)


def get_secret(key: str) -> str:
    try:
        return secrets[key]
    except KeyError:
        raise KeyError(f"Secret '{key}' not found in secrets.json")
