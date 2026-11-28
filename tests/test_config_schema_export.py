import importlib.util
import os

_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "export_config_schema.py")
_spec = importlib.util.spec_from_file_location("export_config_schema", _path)
export = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(export)


def test_checked_in_schema_is_current():
    assert export.OUT.read_text(encoding="utf-8") == export.render(), "run: python scripts/export_config_schema.py"
