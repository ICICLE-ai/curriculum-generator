import os
import sys
import json
import logging
import tempfile
import traceback
from typing import Dict, Any, List, Optional, Tuple

from digitalagedu.core.llm import slide_kit
from digitalagedu.core.llm.visuals import visual_kit
from digitalagedu.core.llm.presentation_prompts import SUBPROCESS_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


class SafeTelemetryDict(dict):
    """Typo-tolerant dictionary wrapper for telemetry."""
    def __init__(self, data=None):
        super().__init__()
        if data and isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, dict):
                    self[k] = SafeTelemetryDict(v)
                elif isinstance(v, list):
                    self[k] = [SafeTelemetryDict(item) if isinstance(item, dict) else item for item in v]
                else:
                    self[k] = v

    def __getitem__(self, key):
        if not isinstance(key, str):
            return super().get(key, SafeTelemetryDict())
        if key in self:
            return super().__getitem__(key)
        for k, v in self.items():
            if isinstance(k, str) and k.lower() == key.lower():
                return v
        return SafeTelemetryDict()

    def get(self, key, default=None):
        try:
            val = self[key]
            if isinstance(val, SafeTelemetryDict) and len(val) == 0:
                return default
            return val
        except Exception:
            return default

    def __getattr__(self, name):
        return self[name]


class SlideDeckRepl:
    """
    Stateful Interactive REPL sandbox for incremental slide and visual asset construction.
    Maintains active pptx.Presentation, slide_kit, visual_kit, and telemetry state across turns.
    """

    def __init__(
        self,
        output_path: str,
        telemetry: Dict[str, Any],
        solution_code: str,
        temp_dir: str
    ):
        self.output_path = output_path
        self.telemetry = telemetry
        self.solution_code = solution_code
        self.temp_dir = temp_dir
        self.history: List[str] = []

        # Local execution namespace
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.dml.color import RGBColor

        self.prs = Presentation()
        self.prs.slide_width = Inches(slide_kit.SLIDE_WIDTH_INCHES)
        self.prs.slide_height = Inches(slide_kit.SLIDE_HEIGHT_INCHES)

        assets_dir = os.path.join(os.path.dirname(os.path.abspath(output_path)), "presentation_assets")
        os.makedirs(assets_dir, exist_ok=True)
        visual_kit.output_dir = assets_dir

        self.safe_telemetry = SafeTelemetryDict(telemetry)
        self.visual_assets: Dict[str, Any] = {}

        # Matplotlib headless setup
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        # Register in sys.modules so 'import slide_kit' and 'import visual_kit' work directly
        sys.modules["slide_kit"] = slide_kit
        sys.modules["visual_kit"] = visual_kit

        # Initial namespace binding
        self.scope = {
            "os": os,
            "sys": sys,
            "json": json,
            "pptx": __import__("pptx"),
            "Presentation": Presentation,
            "Inches": Inches,
            "Pt": Pt,
            "RGBColor": RGBColor,
            "slide_kit": slide_kit,
            "Theme": slide_kit.Theme,
            "visual_kit": visual_kit,
            "Colors": visual_kit.Colors,
            "plt": plt,
            "np": np,
            "prs": self.prs,
            "telemetry": self.safe_telemetry,
            "solution_code": self.solution_code,
            "visual_assets": self.visual_assets,
            "slides": [],
        }

    def get_deck_summary(self) -> str:
        """Returns a concise summary of existing slides in the deck to prevent duplication."""
        if not self.prs.slides:
            return "No slides created yet. Canvas is blank."
        items = []
        for idx, s in enumerate(self.prs.slides):
            title = "Untitled"
            for sh in s.shapes:
                if sh.has_text_frame and sh.text_frame.text.strip():
                    first_line = [l.strip() for l in sh.text_frame.text.strip().split("\n") if l.strip()]
                    if first_line:
                        title = first_line[0][:32]
                        break
            items.append(f"Slide {idx+1}: '{title}'")
        return f"Current Slides in Deck ({len(self.prs.slides)}): " + ", ".join(items)

    def execute_snippet(self, code_snippet: str) -> Tuple[bool, str]:
        """
        Executes a Python code chunk within the persistent presentation scope.
        Returns (success: bool, output_or_error_message: str).
        """
        cleaned = code_snippet.strip()
        if cleaned.startswith("```python"):
            cleaned = cleaned[len("```python"):].strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:].strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

        # Capture stdout & stderr
        import io
        from contextlib import redirect_stdout, redirect_stderr

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        try:
            with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                exec(cleaned, self.scope)
            self.history.append(cleaned)
            out_str = stdout_buf.getvalue().strip()
            err_str = stderr_buf.getvalue().strip()
            combined = f"{out_str}\n{err_str}".strip() if err_str else (out_str or "Success: Step executed cleanly.")
            return True, combined
        except Exception as e:
            tb = traceback.format_exc()
            return False, f"Execution Error: {e}\n{tb}"

    def finalize(self) -> bool:
        """Saves the presentation to the target output path."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.output_path)), exist_ok=True)
            self.prs.save(self.output_path)
            return os.path.exists(self.output_path) and os.path.getsize(self.output_path) > 0
        except Exception as e:
            logger.error(f"Failed to save final presentation deck: {e}")
            return False


def execute_presentation_code_sandbox(
    python_code: str,
    output_path: str,
    telemetry: Optional[Dict[str, Any]] = None,
    solution_code: str = "",
    timeout: int = SUBPROCESS_TIMEOUT_SECONDS
) -> Tuple[bool, str]:
    """
    Backwards-compatible execution sandbox using SlideDeckRepl.
    Executes a script and calls build_presentation(prs, slide_kit, visual_kit, telemetry, solution_code) if defined.
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            repl = SlideDeckRepl(
                output_path=output_path,
                telemetry=telemetry or {},
                solution_code=solution_code,
                temp_dir=temp_dir
            )
            ok, msg = repl.execute_snippet(python_code)
            if not ok:
                return False, msg

            if "build_presentation" in repl.scope and callable(repl.scope["build_presentation"]):
                try:
                    repl.scope["build_presentation"](
                        prs=repl.prs,
                        slide_kit=repl.scope["slide_kit"],
                        visual_kit=repl.scope["visual_kit"],
                        telemetry=repl.safe_telemetry,
                        solution_code=repl.solution_code
                    )
                except Exception as call_e:
                    return False, f"build_presentation error: {call_e}\n{traceback.format_exc()}"

            saved = repl.finalize()
            if not saved:
                return False, "Failed to save generated presentation to disk."
            return True, f"Successfully created presentation: {output_path}"
    except Exception as e:
        return False, f"Sandbox error: {e}\n{traceback.format_exc()}"

