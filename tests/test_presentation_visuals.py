import os
import tempfile
import pytest
from pptx import Presentation

from digitalagedu.core.llm import slide_kit
from digitalagedu.core.llm.visuals import visual_kit
from digitalagedu.core.llm.presentation_designer import execute_presentation_code_sandbox


def test_visual_kit_3d_and_charts():
    """Verifies that 3D surface and diagnostic charts render and cache properly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Override assets dir for test isolation
        visual_kit.output_dir = temp_dir

        # 1. 3D surface orbit
        vid_path, poster_path = visual_kit.render_3d_surface_orbit(
            surface_type="saddle",
            title="Test Saddle Optimization",
            frames=10,
            fps=12
        )
        assert os.path.exists(vid_path), "3D surface MP4 was not created"
        assert os.path.exists(poster_path), "3D surface poster PNG was not created"
        assert os.path.getsize(vid_path) > 0

        # Caching check
        vid_path2, poster_path2 = visual_kit.render_3d_surface_orbit(
            surface_type="saddle",
            title="Test Saddle Optimization",
            frames=10,
            fps=12
        )
        assert vid_path == vid_path2

        # 2. Diagnostic ROC curve
        roc_path = visual_kit.render_roc_curve(auc_score=0.95, title="Test ROC")
        assert os.path.exists(roc_path)
        assert os.path.getsize(roc_path) > 0


def test_visual_kit_network_flow():
    """Verifies network architecture animation generation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        visual_kit.output_dir = temp_dir
        vid_path, poster_path = visual_kit.render_network_flow(
            stage_names=["Input", "Encoder", "Classifier"],
            frames=8,
            fps=12
        )
        assert os.path.exists(vid_path)
        assert os.path.exists(poster_path)


def test_slide_kit_media_embedding():
    """Verifies that add_video and add_image correctly embed media into a Presentation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        visual_kit.output_dir = temp_dir
        vid_path, poster_path = visual_kit.render_3d_surface_orbit(frames=6, fps=12)
        roc_path = visual_kit.render_roc_curve(auc_score=0.92)

        prs = Presentation()
        slide = slide_kit.create_slide(prs)
        slide_kit.add_header(slide, "TEST", "Visual Toolkit Integration Test")

        # Embed video
        movie = slide_kit.add_video(slide, x=0.8, y=2.0, w=5.5, h=4.5, video_path=vid_path, poster_image_path=poster_path)
        assert movie is not None

        # Embed image
        pic = slide_kit.add_image(slide, x=6.6, y=2.0, w=5.8, h=4.5, image_path=roc_path, caption="ROC Diagnostic")
        assert pic is not None

        output_pptx = os.path.join(temp_dir, "test_presentation.pptx")
        prs.save(output_pptx)
        assert os.path.exists(output_pptx)
        assert os.path.getsize(output_pptx) > 0


def test_execute_presentation_sandbox():
    """Verifies sandboxed subprocess execution with slide_kit and visual_kit."""
    sample_code = """
import pptx
import slide_kit
import visual_kit

def build_presentation(prs, slide_kit, visual_kit, telemetry, solution_code):
    s = slide_kit.create_slide(prs)
    slide_kit.add_header(s, "WEEK 1", "Autonomous Presentation Sandbox")
    slide_kit.add_card(s, 0.8, 2.0, 11.7, 4.5, title="Subprocess Execution", body="Verified end-to-end sandbox.")
"""
    with tempfile.TemporaryDirectory() as temp_dir:
        out_deck = os.path.join(temp_dir, "sandbox_deck.pptx")
        success, msg = execute_presentation_code_sandbox(
            python_code=sample_code,
            output_path=out_deck,
            telemetry={"run_summary": {"accuracy": "91.2%"}},
            solution_code="print('Hello World')",
            timeout=180
        )
        assert success is True, f"Sandbox execution failed: {msg}"
        assert os.path.exists(out_deck)
        assert os.path.getsize(out_deck) > 0


def test_execute_presentation_sandbox_error_handling():
    """Verifies that syntax or execution errors inside the script are caught cleanly without crashing."""
    bad_code = """
def build_presentation(prs, slide_kit, visual_kit, telemetry, solution_code):
    raise ValueError("Intentional script error to test non-fatal handling")
"""
    with tempfile.TemporaryDirectory() as temp_dir:
        out_deck = os.path.join(temp_dir, "bad_deck.pptx")
        success, err = execute_presentation_code_sandbox(
            python_code=bad_code,
            output_path=out_deck,
            telemetry={},
            solution_code="",
            timeout=45
        )
        assert success is False
        assert "Intentional script error" in err

