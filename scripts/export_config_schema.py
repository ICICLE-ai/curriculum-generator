"""Write RootConfig's JSON schema for the frontend assistant: python scripts/export_config_schema.py"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "frontend" / "src" / "data" / "rootConfigSchema.json"

# Load config.py directly: importing the digitalagedu package pulls in the whole pipeline
_spec = importlib.util.spec_from_file_location("_config", ROOT / "digitalagedu" / "core" / "config.py")
_config = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_config)


def render() -> str:
    return json.dumps(_config.RootConfig.model_json_schema(), indent=2) + "\n"


if __name__ == "__main__":
    OUT.write_text(render(), encoding="utf-8", newline="\n")
