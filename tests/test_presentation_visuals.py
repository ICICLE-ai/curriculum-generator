import os
import tempfile
try:
    import pytest
except ImportError:
    pytest = None
from pptx import Presentation

from digitalagedu.core.llm import slide_kit
from digitalagedu.core.llm.visuals import visual_kit
from digitalagedu.core.llm.presentation_designer import execute_presentation_code_sandbox, SlideDeckRepl


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


def test_slide_deck_repl():
    """Verifies multi-turn interactive REPL session with persistent prs canvas and visual assets."""
    with tempfile.TemporaryDirectory() as temp_dir:
        out_deck = os.path.join(temp_dir, "repl_deck.pptx")
        telemetry = {
            "run_summary": {"accuracy": "93.4%", "auc_roc": "0.981"},
            "contrastive_samples": {
                "top_success": {"image_path": "sample1.jpg", "ground_truth": "Class_A"},
                "hard_failure": {"image_path": "sample2.jpg", "ground_truth": "Class_B", "predicted_class": "Class_A"}
            }
        }
        solution_code = "import torch\ndef forward(x): return x * 2"

        repl = SlideDeckRepl(
            output_path=out_deck,
            telemetry=telemetry,
            solution_code=solution_code,
            temp_dir=temp_dir
        )

        # Turn 1: Asset generation
        step1_code = """
roc_path = visual_kit.render_roc_curve(auc_score=0.98, title="REPL ROC Diagnostic")
visual_assets["roc"] = roc_path
print(f"Generated asset: {roc_path}")
"""
        ok1, msg1 = repl.execute_snippet(step1_code)
        assert ok1 is True, f"Turn 1 failed: {msg1}"
        assert "roc" in repl.visual_assets
        assert os.path.exists(repl.visual_assets["roc"])

        # Turn 2: Slide 1 construction
        step2_code = """
s1 = slide_kit.create_slide(prs)
slide_kit.add_header(s1, "WEEK 1", "REPL Architecture Overview", "Dynamic multi-turn pipeline")
slide_kit.add_metric_card(s1, 0.8, 2.0, 3.6, 1.8, "ACCURACY", "93.4%", subtext="Phase 1 Pipeline")
slide_kit.add_code_box(s1, 4.8, 2.0, 7.7, 4.5, code=solution_code, title="Model Forward Pass")
print("Slide 1 built successfully")
"""
        ok2, msg2 = repl.execute_snippet(step2_code)
        assert ok2 is True, f"Turn 2 failed: {msg2}"
        assert len(repl.prs.slides) == 1

        # Turn 3: Error resilience check (syntax/runtime error caught without crashing REPL)
        bad_snippet = """
this is invalid python syntax ::: !!!
"""
        ok3, err3 = repl.execute_snippet(bad_snippet)
        assert ok3 is False, "Expected error on bad snippet"
        assert "Execution Error" in err3 or "SyntaxError" in err3
        assert len(repl.prs.slides) == 1, "Slide count should not be corrupted by failed turn"

        # Turn 4: Slide 2 construction embedding asset from Turn 1
        step4_code = """
s2 = slide_kit.create_slide(prs)
slide_kit.add_header(s2, "DIAGNOSTICS", "ROC Performance & Decision Thresholds")
slide_kit.add_image(s2, 0.8, 2.0, 6.0, 4.8, image_path=visual_assets["roc"], caption="Test ROC Curve")
slide_kit.add_card(s2, 7.2, 2.0, 5.3, 4.8, title="Ablation Findings", body="Decision threshold aligns with empirical AUC.")
print("Slide 2 built successfully")
"""
        ok4, msg4 = repl.execute_snippet(step4_code)
        assert ok4 is True, f"Turn 4 failed: {msg4}"
        assert len(repl.prs.slides) == 2

        # Finalize
        final_ok = repl.finalize()
        assert final_ok is True
        assert os.path.exists(out_deck)
        assert os.path.getsize(out_deck) > 0


if __name__ == "__main__":
    print("Running test_visual_kit_3d_and_charts...")
    test_visual_kit_3d_and_charts()
    print("Running test_visual_kit_network_flow...")
    test_visual_kit_network_flow()
    print("Running test_slide_kit_media_embedding...")
    test_slide_kit_media_embedding()
    print("Running test_execute_presentation_sandbox...")
    test_execute_presentation_sandbox()
    print("Running test_execute_presentation_sandbox_error_handling...")
    test_execute_presentation_sandbox_error_handling()
    print("Running test_slide_deck_repl...")
    test_slide_deck_repl()
    print("\nALL PRESENTATION VISUAL & REPL TESTS PASSED SUCCESSFULLY!")


