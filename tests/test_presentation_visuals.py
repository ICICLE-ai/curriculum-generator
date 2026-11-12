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


def test_custom_graphic_generation_and_clamping():
    """Verifies that bespoke matplotlib figures and coordinate clamping work properly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        visual_kit.output_dir = temp_dir

        # 1. Test create_figure and save_figure
        fig, ax = visual_kit.create_figure(width=6.0, height=4.0, title="Custom Concept Diagram")
        ax.plot([1, 2, 3], [4, 5, 6], color=visual_kit.Colors.CYAN, lw=2.5)
        ax.annotate("Peak", xy=(3, 6), color=visual_kit.Colors.EMERALD)
        out_img = visual_kit.save_figure(fig, filename="custom_concept.png")
        assert os.path.exists(out_img)
        assert os.path.getsize(out_img) > 0

        # 2. Test slide bounds clamping and layout helpers
        prs = Presentation()
        s = slide_kit.create_slide(prs)
        slide_kit.add_header(s, "CONCEPT", "Neural Feature Map Slicing")

        # Test add_hero_graphic with coordinate overflow (> 7.5 in height)
        hero = slide_kit.add_hero_graphic(s, out_img, x=0.8, y=1.9, w=7.2, h=8.0)
        assert hero is not None
        # Verify clamped height
        assert hero.top.inches + hero.height.inches <= 7.2

        # Test add_callout_column
        callouts = [("Stage 1", "Raw RGB input data"), ("Stage 2", "Feature extraction")]
        cards = slide_kit.add_callout_column(s, callouts, x=8.5, y=1.9, w=4.0, h=5.0)
        assert len(cards) == 2

        # 3. Test SlideDeckRepl get_deck_summary
        out_deck = os.path.join(temp_dir, "test_deck.pptx")
        repl = SlideDeckRepl(out_deck, {}, "", temp_dir)
        step_code = """
s1 = slide_kit.create_slide(prs)
slide_kit.add_header(s1, "INTRO", "Domain Introduction")
"""
        repl.execute_snippet(step_code)
        deck_summary = repl.get_deck_summary()
        assert "Slide 1: 'INTRO'" in deck_summary or "Slide 1" in deck_summary
        assert "Current Slides in Deck (1)" in deck_summary


def test_high_level_diagram_helpers_and_dark_theme():
    """Verifies that high-level diagram helpers produce valid, aesthetic figures with proper contrast."""
    with tempfile.TemporaryDirectory() as temp_dir:
        visual_kit.output_dir = temp_dir

        # 1. Flowchart
        flow_path = visual_kit.draw_flowchart(
            steps=[
                ("Data Ingestion", "Load and normalize image tensors"),
                ("Feature Extractor", "DINOv2 ViT backbone forward pass"),
                ("Diagnostic Head", "Softmax classification projection")
            ],
            title="Computational Pipeline Workflow",
            subtitle="Stage 1 to Stage 3 Data Transformations"
        )
        assert os.path.exists(flow_path)
        assert os.path.getsize(flow_path) > 1000

        # 2. Architecture
        arch_path = visual_kit.draw_architecture(
            layers=[
                {"name": "Input Batch", "detail": "(B, 3, 224, 224)", "op": "Raw RGB"},
                {"name": "ViT Backbone", "detail": "DINOv2 (768-d)", "op": "Frozen Features"},
                {"name": "Linear Classifier", "detail": "fc1(768 -> 2)", "op": "CrossEntropy"}
            ],
            title="Deep Learning Architecture & Tensor Contracts"
        )
        assert os.path.exists(arch_path)
        assert os.path.getsize(arch_path) > 1000

        # 3. Confusion Matrix (both with None and with custom matrix)
        cm_none_path = visual_kit.draw_confusion_matrix(matrix=None, class_names=["Benign", "Malignant"])
        assert os.path.exists(cm_none_path)
        assert os.path.getsize(cm_none_path) > 1000

        cm_custom_path = visual_kit.draw_confusion_matrix(
            matrix=[[450, 50], [30, 470]],
            class_names=["Benign", "Malignant"],
            title="Empirical Diagnostic Confusion Matrix"
        )
        assert os.path.exists(cm_custom_path)
        assert os.path.getsize(cm_custom_path) > 1000

        # 4. Metric Comparison
        metric_path = visual_kit.draw_metric_comparison(
            metrics={"Accuracy": 92.4, "AUC-ROC": 97.1, "Precision": 89.8, "Recall": 93.5},
            title="Cross-Validation Diagnostic Performance"
        )
        assert os.path.exists(metric_path)
        assert os.path.getsize(metric_path) > 1000

        # 5. Distribution (donut with bright text)
        dist_path = visual_kit.draw_distribution(
            class_counts={"Benign": 1800, "Malignant": 1497},
            title="Dataset Class Balance",
            kind="donut"
        )
        assert os.path.exists(dist_path)
        assert os.path.getsize(dist_path) > 1000

        # 6. SafeTelemetryDict never invents data: missing keys raise with the real keys listed
        from digitalagedu.core.llm.slide_deck_repl import SafeTelemetryDict
        safe_dict = SafeTelemetryDict({"Run_Summary": {"auc_roc": 0.99}})
        assert safe_dict.get("confusion") is None
        assert safe_dict["run_summary"]["AUC_ROC"] == 0.99
        try:
            safe_dict["confusion_matrix"]
            raise AssertionError("expected KeyError")
        except KeyError as e:
            assert "Run_Summary" in str(e)


def _lesson_plan(**overrides):
    """A valid 10-slide lesson plan: goal, overview, 2 methods x 2 slides, why, 3 application slides."""
    from digitalagedu.core.llm.presentation_prompts import ConceptVisualSpec, EvidenceItem, LessonPlan, LessonSlide

    def slide(section, title, method=None, code_function=None, evidence=True):
        return LessonSlide(
            section=section, method=method, title=title, teaching_point=f"{title} matters.", explanation=f"{title}, in plain words.",
            on_slide_text=[f"{title}: the key idea", "One short supporting line"],
            visual=ConceptVisualSpec(category="custom_matplotlib", visual_idea="diagram", suggested_recipe_query="diagram"),
            evidence=[EvidenceItem(label="Accuracy", value="94.5%", context="this run")] if evidence else [],
            code_function=code_function, speaker_notes=f"Notes for {title}.",
        )

    fields = dict(
        deck_title="Foliar Lesion Boundary Delineation",
        domain_subtitle="Detecting early-stage bacterial leaf blight in agricultural crops",
        methods=["Channel normalization", "IoU scoring"],
        slides=[
            slide("goal", "Leaves, lesions and what we must mark"),
            slide("overview", "Two steps: normalize, then score", evidence=False),
            slide("method", "What channel normalization is", "Channel normalization", evidence=False),
            slide("method", "How normalization rescales pixels", "Channel normalization", evidence=False),
            slide("method", "What IoU measures", "IoU scoring", evidence=False),
            slide("method", "How IoU is computed", "IoU scoring", evidence=False),
            slide("why", "Raw pixels mislead across lighting", evidence=False),
            slide("application", "Normalized leaves from this run"),
            slide("application", "This run's IoU results"),
            slide("application", "The verified IoU code", code_function="compute_iuo"),  # misspelled: closest match is used
        ],
        takeaways=["Normalization stabilizes features.", "IoU quantifies lesion overlap."],
    )
    fields.update(overrides)
    return LessonPlan(**fields)


# One slide's code for every planned slide: a real-data chart, the slide's own text, and the verified code if any
_SLIDE_CODE = '''slide = slide_kit.create_slide(prs)
slide_kit.add_header(slide, tag=slide_spec.section.upper(), title=slide_spec.title)
fig, ax = plt.subplots(figsize=(7.0, 3.2))
balance = telemetry["run_summary"]["class_balance"]
ax.bar(list(balance), list(balance.values()))
plt.savefig("slide.png")
plt.close(fig)
slide_kit.add_image(slide, 0.6, 1.9, 6.5, 3.0, image_path="slide.png")
slide_kit.add_card(slide, 7.4, 1.9, 5.4, 3.0, title="Key points", body=" | ".join(slide_spec.on_slide_text))
if code_function_name:
    slide_kit.add_code_box(slide, 0.6, 5.1, 12.2, 1.9, code=solution_excerpt, title=code_function_name)'''


def _slide_of(messages):
    import re
    return int(re.search(r"teaching slide (\d+)'s point", messages[1]["content"]).group(1))


def _replies_by_slide(scripted, default):
    """Fake code-client replies keyed by the slide a request is for, since first attempts are requested
    concurrently: slide n gets its scripted replies in order, then `default`."""
    import threading
    lock, queues = threading.Lock(), {n: list(r) for n, r in scripted.items()}

    def reply(**kwargs):
        with lock:
            queue = queues.get(_slide_of(kwargs["messages"]), [])
            return queue.pop(0) if queue else default
    return reply


def test_lesson_plan_deck_follows_the_plan_with_reviews_and_code_only_in_application(tmp_path, monkeypatch):
    """The deck is the lesson: title, every planned slide in order (goal -> overview -> methods -> why ->
    application), then takeaways; the verified code reaches only application slides."""
    monkeypatch.chdir(tmp_path)  # slide reviews write their renders under ./tmp/slide_review
    from unittest.mock import MagicMock, patch
    from digitalagedu.core.llm.presentation_designer import PresentationDesigner
    from digitalagedu.core.llm.presentation_prompts import SlideReview
    from digitalagedu.core.llm.schemas import Module, ProblemStatementSchema
    from digitalagedu.core.llm.generation_trace import GenerationTrace
    from test_phase2_orchestration import stream

    def fenced(code):
        return stream(f"Slide code:\n```python\n{code}\n```")

    module = Module(id="foliar_necrosis", title="Foliar Lesion Boundary Delineation", week=3,
                    context="Plant pathology foliar necrosis inspection", difficulty="Intermediate")
    problem = ProblemStatementSchema(
        title="Foliar Lesion Boundary Delineation", domain_context="Detecting early-stage bacterial leaf blight",
        problem_statement="Segment damaged tissue and compute IoU", learning_objectives=["Compute binary mask IoU"],
        suggested_focus="Segmentation", markdown_overview="# Overview")
    solution_code = ("def normalize_channels(img):\n    return img / img.max()\n\n"
                     "def compute_iou(a, b):\n    inter = (a & b).sum()\n    return inter / (a | b).sum()\n")
    telemetry = {"run_summary": {"overall_accuracy_percent": 94.5, "class_balance": {"Apple___scab": 13, "Apple___healthy": 40}}}
    plan = _lesson_plan()

    # Without a client there is no deck (no fallbacks)
    assert PresentationDesigner(client=None)._plan_lesson(module, problem, "", {}) is None
    assert PresentationDesigner(client=None).generate_presentation_deck(module, problem, "", {}, "dummy.pptx") is None

    good = fenced(_SLIDE_CODE)
    fabricated = fenced("y = np.random.choice(['Healthy', 'Blight'], size=100)\n" + _SLIDE_CODE)
    accept = SlideReview(acceptable=True)
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = (
        [plan, accept, SlideReview(acceptable=False, issues=["Use a larger font for the key idea"])] + [accept] * 9)
    code_client = MagicMock()
    code_client.chat.completions.create.side_effect = _replies_by_slide({1: [fabricated]}, good)  # slide 1 fakes data once

    with tempfile.TemporaryDirectory() as temp_dir:
        out_deck = os.path.join(temp_dir, "lesson_deck.pptx")
        screenshot = os.path.join(temp_dir, "shot.png")
        import matplotlib.pyplot as plt
        plt.imsave(screenshot, [[0.0, 1.0]])
        trace = GenerationTrace(temp_dir, module.id, "glm-5")
        designer = PresentationDesigner(client=mock_client, code_client=code_client)
        with patch("digitalagedu.core.llm.presentation_designer.render_deck_pngs", return_value=[screenshot, screenshot]):
            assert designer.generate_presentation_deck(module, problem, solution_code, telemetry, out_deck,
                                                       artifacts={"raw_sample": "sample.jpg"}, trace=trace) == out_deck

        assert mock_client.chat.completions.create.call_args_list[0].kwargs["model"] == "deepseek-v4-flash"  # the planner model
        execs = [a for a in trace.doc["activity"].values() if a["prov:type"] == "dage:slide_exec"]
        assert [a["dage:success"] for a in execs] == [False] + [True] * 11
        assert "fabricates data" in execs[0]["dage:error"]
        reviews = [a for a in trace.doc["activity"].values() if a["prov:type"] == "dage:slide_review"]
        assert [a["dage:acceptable"] for a in reviews] == [True, False] + [True] * 9
        calls = [c.kwargs["messages"] for c in code_client.chat.completions.create.call_args_list]
        slide2 = [m for m in calls if _slide_of(m) == 2]
        assert len(slide2) == 2 and any("Use a larger font for the key idea" in m["content"] for m in slide2[1] if m["role"] == "user")
        prompt = lambda n: next(m for m in calls if _slide_of(m) == n)[1]["content"]
        assert "VERIFIED CODE" not in prompt(3) and "REAL RUN DATA" not in prompt(3)  # slide 3: a method slide
        assert "VERIFIED CODE" in prompt(10) and "def compute_iou" in prompt(10)    # slide 10: application with code

        prs = Presentation(out_deck)
        assert len(prs.slides) == 12  # title + 10 planned + takeaways
        texts = [" ".join(sh.text_frame.text for sh in s.shapes if sh.has_text_frame) for s in prs.slides]
        assert [t for t in texts[1:11] if "What channel normalization is" in t]
        assert [i for i, t in enumerate(texts) if "compute_iou(a, b)" in t] == [10]  # the code box only on slide 10
        assert prs.slides[3].notes_slide.notes_text_frame.text == "Notes for What channel normalization is."
        assert "Normalization stabilizes features." in texts[11]

    # A slide that fails 3 times is skipped; the deck fails when fewer than half the planned slides were built
    bad = fenced("raise RuntimeError('Forced test error')")

    def build_deck(code_replies, path):
        plan_client, codes = MagicMock(), MagicMock()
        plan_client.chat.completions.create.side_effect = [plan]
        codes.chat.completions.create.side_effect = code_replies
        return PresentationDesigner(client=plan_client, code_client=codes).generate_presentation_deck(
            module, problem, solution_code, telemetry, path)

    with tempfile.TemporaryDirectory() as temp_dir:
        partial = os.path.join(temp_dir, "partial.pptx")
        assert build_deck(_replies_by_slide({2: [bad, bad, bad]}, good), partial) == partial
        assert len(Presentation(partial).slides) == 11  # slide 2 skipped
        failed = os.path.join(temp_dir, "failed.pptx")
        with pytest.raises(RuntimeError, match="Only 0 of 10 planned slides"):
            build_deck(_replies_by_slide({}, bad), failed)
        assert not os.path.exists(failed)


def test_lesson_plan_enforces_the_teaching_flow():
    import pytest
    from pydantic import ValidationError
    plan = _lesson_plan()
    slides = plan.slides
    with pytest.raises(ValidationError, match="section order"):
        _lesson_plan(slides=[slides[2], slides[3], slides[0], slides[1]] + slides[4:])  # methods before the goal
    with pytest.raises(ValidationError, match="'IoU scoring' has 1 explanation slides"):
        _lesson_plan(slides=slides[:5] + slides[6:] + [slides[-1]])  # drop one IoU slide, keep 10
    with pytest.raises(ValidationError, match="only application slides may set `code_function`"):
        _lesson_plan(slides=slides[:2] + [slides[2].model_copy(update={"code_function": "compute_iou"})] + slides[3:])
    with pytest.raises(ValidationError, match="need at least one real number"):
        _lesson_plan(slides=[slides[0].model_copy(update={"evidence": []})] + slides[1:])

    # Run 49088b7e: slides used shortened or reworded forms of the plan's own method names
    reworded = [s.model_copy(update={"method": {"Channel normalization": "channel normalisation", "IoU scoring": "IoU"}[s.method]})
                if s.section == "method" else s for s in slides]
    loose = _lesson_plan(methods=["Channel normalization (per-channel z-score)", "IoU scoring"], slides=reworded)
    assert [s.method for s in loose.slides if s.section == "method"] == [
        "Channel normalization (per-channel z-score)"] * 2 + ["IoU scoring"] * 2  # mapped to the listed names
    with pytest.raises(ValidationError, match=r"match nothing in `methods`"):
        _lesson_plan(slides=slides[:2] + [slides[2].model_copy(update={"method": "Random forests"})] + slides[3:])

    # Run f73310e1: rewritten plans dropped `method` or sent "None"; unnamed slides fill the methods short of slides
    unnamed = [s.model_copy(update={"method": "None" if i % 2 else None}) if s.section == "method" else s
               for i, s in enumerate(slides)]
    assert [s.method for s in _lesson_plan(slides=unnamed).slides if s.section == "method"] == [
        "Channel normalization"] * 2 + ["IoU scoring"] * 2
    with pytest.raises(ValidationError, match=r"method slides now: 'What channel normalization is' -> 'Channel normalization'"):
        _lesson_plan(slides=slides[:4] + [s.model_copy(update={"section": "why"}) for s in slides[4:7]] + slides[7:])


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
    print("Running test_custom_graphic_generation_and_clamping...")
    test_custom_graphic_generation_and_clamping()
    print("Running test_high_level_diagram_helpers_and_dark_theme...")
    test_high_level_diagram_helpers_and_dark_theme()
    print("\nALL PRESENTATION VISUAL, REPL & DESIGNER TESTS PASSED SUCCESSFULLY!")





def test_missing_image_fails_the_snippet_and_leaves_no_half_built_slide():
    """add_image used to draw an '[Asset Placeholder: ...]' card that shipped as slide content."""
    from digitalagedu.core.llm.slide_deck_repl import SlideDeckRepl
    with tempfile.TemporaryDirectory() as temp_dir:
        repl = SlideDeckRepl(os.path.join(temp_dir, "deck.pptx"), {}, "", temp_dir)
        ok, msg = repl.execute_snippet(
            "slide_kit.add_split_slide(prs, title='T', left_content=['a'], image_path='missing_chart.png')"
        )
        assert not ok and "image not found: 'missing_chart.png'" in msg
        assert len(repl.prs.slides) == 0  # the slide created before the error was rolled back
        ok, _ = repl.execute_snippet("slide_kit.add_split_slide(prs, title='T', left_content=['a'])")
        assert ok and len(repl.prs.slides) == 1 and repl.finalize()


def test_apply_dark_theme_accepts_subplot_grids_and_missing_ax():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    for call in (lambda fig, axes: visual_kit.apply_dark_theme(fig, axes),  # array from plt.subplots(1, 3)
                 lambda fig, axes: visual_kit.apply_dark_theme(fig)):       # ax omitted: all axes
        fig, axes = plt.subplots(1, 3)
        call(fig, axes)
        assert all(ax.get_facecolor() == matplotlib.colors.to_rgba(visual_kit.Colors.CARD) for ax in axes)
        plt.close(fig)


def test_planner_rejects_names_as_evidence_values():
    import pytest
    from pydantic import ValidationError
    from digitalagedu.core.llm.presentation_prompts import EvidenceItem
    # Run dc3f8936: a class name as a metric value wrapped off its card
    with pytest.raises(ValidationError, match="number of at most 16 characters"):
        EvidenceItem(label="Class", value="Tomato___Early_blight", context="poor segmentation")
    assert EvidenceItem(label="Images", value="13 images", context="Apple___scab").value == "13 images"


def test_code_excerpt_fits_the_slide_code_box_after_wrapping():
    from digitalagedu.core.llm.presentation_prompts import solution_excerpt
    long_line = "    plt.imshow(segmented, cmap='gray', alpha=0.3, interpolation='nearest', origin='upper')\n"  # wraps to 2 rows
    code = "def compare(original, segmented):\n" + long_line * 6 + "    return None\n"
    name, excerpt = solution_excerpt(code, "compare")
    rows = sum(max(1, -(-len(l) // 64)) for l in excerpt.splitlines())
    assert name == "compare" and rows <= 8 and excerpt.endswith("    ...")
    short = "def f(x):\n    return x\n"
    assert solution_excerpt(short, "f") == ("f", short.strip())


def test_dense_layout_keeps_long_text_inside_cards_and_charts_unstretched():
    """A run's deck had text spilling past its cards and the header and a wide chart squashed to the box."""
    from types import SimpleNamespace
    from pptx.enum.text import MSO_AUTO_SIZE
    from digitalagedu.core.llm.slide_kit.theme import _text_height_pt
    # The old concept template: the densest layout slide_kit has to fit
    dense_layout = '''slide = slide_kit.create_slide(prs)
slide_kit.add_header(slide, tag="CONCEPT 2", title=concept.title, subtitle=concept.domain_application)
fig, ax = plt.subplots(figsize=(7.0, 3.1))
visual_kit.apply_dark_theme(fig, ax)
ax.bar(["a", "b"], [1, 2])
fig.set_size_inches(11.3, 4.6)
plt.savefig("concept_2.png", dpi=150, facecolor=fig.get_facecolor())
plt.close(fig)
slide_kit.add_image(slide, 0.6, 1.75, 6.5, 2.9, image_path="concept_2.png")
slide_kit.add_callout_banner(slide, 0.6, 4.75, 6.5, 0.95, text=concept.formula_or_rule, title="RULE")
slide_kit.add_callout_banner(slide, 0.6, 5.8, 6.5, 1.3, text=concept.misconception, title="COMMON MISCONCEPTION")
for i, ev in enumerate(concept.real_evidence[:2]):
    slide_kit.add_metric_card(slide, 7.35 + i * 2.8, 1.75, 2.65, 1.05, label=ev.label, value=ev.value, subtext=ev.context)
slide_kit.add_code_box(slide, 7.35, 2.9, 5.45, 1.9, code=solution_excerpt, title=code_function_name + "()  - verified solution")
slide_kit.add_callout_column(slide, [("Why", concept.key_takeaways[0]), ("How", concept.key_takeaways[-1])], x=7.35, y=4.9, w=5.45, h=2.2)'''
    long = "Students often confuse yellowing from senescence with chlorosis caused by infection, " * 4  # ~340 chars
    concept = SimpleNamespace(
        title="RGB Channel Decomposition & Symptom Pixel Partitioning",
        domain_application=long[:260], formula_or_rule=long[:120], misconception=long[:305],
        key_takeaways=[long[:170], long[:215]],
        real_evidence=[SimpleNamespace(label="MEAN GREEN FRACTION (HEALTHY BASELINE)", value="0.75", context=long[:60])] * 2,
    )
    code = "\n".join(f"    channel_{i} = image[..., {i % 3}].astype(float) / 255.0" for i in range(24))
    with tempfile.TemporaryDirectory() as temp_dir:
        repl = SlideDeckRepl(os.path.join(temp_dir, "deck.pptx"), {}, "", temp_dir)
        repl.scope.update(concept=concept, code_function_name="split_channels", solution_excerpt=code)
        ok, msg = repl.execute_snippet(dense_layout)
        assert ok, msg
        shapes = list(repl.prs.slides[0].shapes)
        E = 914400
        for sh in shapes[1:]:  # [0] is the full-slide background
            assert sh.top + sh.height <= 7.1 * E + 1 and sh.left + sh.width <= 12.84 * E, sh.name
            if sh.shape_type == 17:  # text box: fits its own box by estimate (grown if shrinking was not enough)
                tf = sh.text_frame
                assert tf.auto_size == MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE, sh.name
                sizes = [p.font.size.pt for p in tf.paragraphs]
                assert min(sizes) >= 8 and _text_height_pt(tf.paragraphs, sizes, sh.width / E - 0.2) <= (sh.height / E - 0.1) * 72, sh.name
        header = next(sh for sh in shapes if sh.shape_type == 17)
        assert header.top + header.height <= 1.7 * E
        pic = next(sh for sh in shapes if sh.shape_type == 13)
        assert abs(pic.width / pic.height - 11.3 / 4.6) < 0.02 and pic.left >= 0.6 * E and pic.top >= 1.75 * E


def test_planner_keeps_long_text_whole():
    from digitalagedu.core.llm.presentation_prompts import EvidenceItem
    # Run f73310e1: rejecting a 91-character context failed the whole deck; run ee09eaac: cutting it showed '…'.
    # Long text now stays whole for the shortening call and slide_kit's growing boxes
    assert EvidenceItem(label="Rarest class", value="13", context="x" * 91).context == "x" * 91
    # ...and a label stuffed into the value keeps just its number
    assert EvidenceItem(label="Rows", value="Total Rows Processed: 500", context="results.csv").value == "500"


def test_visual_kit_colors_resolve_guessed_names():
    C = visual_kit.Colors
    assert (C.TEXT_MUTED, C.SURFACE, C.TEXT_LIGHT, C.ACCENT, C.TEXT_PRIMARY) == (C.MUTED, C.CARD, C.TEXT, C.CYAN, C.TEXT)
    assert C.HIGHLIGHT == C.GOLD and C.BACKGROUND == C.BG and C.CORAL == "#EF4444"
    assert not hasattr(C, "__wrapped__")


def test_layout_issues_flag_partial_overlaps_but_not_nested_text():
    from digitalagedu.core.llm.slide_kit.theme import layout_issues
    prs = Presentation()
    slide = slide_kit.create_slide(prs)
    slide_kit.add_card(slide, 0.6, 2.0, 5.0, 0.5, title="Short card", body="text fits inside its own card")
    slide_kit.add_card(slide, 7.0, 2.0, 5.0, 2.0, title="Right", body="no overlap")
    assert layout_issues(slide) == []
    slide_kit.add_metric_card(slide, 4.0, 2.2, 2.5, 1.0, label="Accuracy", value="91%")
    issues = layout_issues(slide)
    assert len(issues) == 1 and "'Short card'" in issues[0] and "'ACCURACY'" in issues[0]


def _fresh_renderer(monkeypatch):
    from digitalagedu.core.llm import slide_render
    monkeypatch.setattr(slide_render, "_disabled_reason", None)
    monkeypatch.setattr(slide_render, "_mode", None)
    monkeypatch.setattr(slide_render, "_profiles", {})
    monkeypatch.setattr(slide_render, "_failures", 0)
    monkeypatch.setattr(slide_render.shutil, "which", lambda name: f"/usr/bin/{name}")
    return slide_render


def test_failed_render_disables_rendering_for_the_rest_of_the_run(tmp_path, monkeypatch):
    """Run 49088b7e: each of 35 failing renders hung until the timeout, about 50 min per deck."""
    import subprocess
    slide_render = _fresh_renderer(monkeypatch)
    calls = []

    def hangs(cmd, **kwargs):
        calls.append(kwargs)
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    monkeypatch.setattr(slide_render.subprocess, "run", hangs)
    deck = tmp_path / "d.pptx"
    deck.write_bytes(b"")
    assert slide_render.render_deck_pngs(str(deck), str(tmp_path)) == []
    assert slide_render.render_deck_pngs(str(deck), str(tmp_path)) == []  # skipped: no further soffice calls
    # one cold start per mode, each with its own profile; only the job_folder mode keeps the default TMPDIR
    assert len(calls) == len(slide_render.RENDER_MODES)
    assert all(k["timeout"] == slide_render.FIRST_SOFFICE_TIMEOUT_S for k in calls)
    assert all(k["env"]["XDG_RUNTIME_DIR"] == k["env"]["HOME"] for k in calls)
    assert [k["env"].get("TMPDIR") == k["env"]["HOME"] for k in calls] == [True, False, True]
    assert all(m in slide_render._disabled_reason for m in slide_render.RENDER_MODES)  # every mode's error is logged


def test_render_falls_back_to_node_tmp_and_keeps_using_it(tmp_path, monkeypatch):
    """Runs 0ffa9ff2, f73310e1, ee09eaac: LibreOffice could not save the PDF in the job's Lustre folder."""
    import subprocess
    slide_render = _fresh_renderer(monkeypatch)
    out_dir, calls = tmp_path / "review", []
    out_dir.mkdir()
    deck = out_dir / "d.pptx"
    deck.write_bytes(b"pptx")

    def lustre_fails(cmd, **kwargs):
        calls.append(cmd)
        if cmd[0] == "pdftoppm":
            (out_dir / "slide-1.png").write_bytes(b"png")
        elif cmd[cmd.index("--outdir") + 1] == str(out_dir):
            raise subprocess.CalledProcessError(1, cmd, stderr=b"0x507(Error Area:Io Class:Access Code:7)")

    monkeypatch.setattr(slide_render.subprocess, "run", lustre_fails)
    for _ in range(2):
        assert slide_render.render_deck_pngs(str(deck), str(out_dir)) == [str(out_dir / "slide-1.png")]
    soffice = [c for c in calls if c[0] != "pdftoppm"]
    assert len(soffice) == 4 and slide_render._mode == "node_tmp"  # 2 failed modes, then node_tmp twice
    node_dir = soffice[2][soffice[2].index("--outdir") + 1]
    assert soffice[2][-1] == os.path.join(node_dir, "d.pptx") and os.path.isfile(soffice[2][-1])  # deck copied out
    assert soffice[3][1] == soffice[2][1]  # the same profile reused


def test_later_renders_reuse_the_profile_with_the_short_timeout(tmp_path, monkeypatch):
    """LibreOffice's first start overran 45 s on Lustre and disabled every review (run 0ffa9ff2)."""
    slide_render = _fresh_renderer(monkeypatch)
    calls = []

    def renders(cmd, **kwargs):
        calls.append((cmd, kwargs))
        if cmd[0] == "pdftoppm":
            (tmp_path / "slide-1.png").write_bytes(b"png")

    monkeypatch.setattr(slide_render.subprocess, "run", renders)
    for _ in range(2):
        assert slide_render.render_deck_pngs(str(tmp_path / "d.pptx"), str(tmp_path)) == [str(tmp_path / "slide-1.png")]
    soffice = [(c, k) for c, k in calls if c[0] != "pdftoppm"]
    assert [k["timeout"] for _, k in soffice] == [slide_render.FIRST_SOFFICE_TIMEOUT_S, slide_render.SOFFICE_TIMEOUT_S]
    assert soffice[0][0][1] == soffice[1][0][1]  # the same -env:UserInstallation profile


def test_working_renderer_skips_only_slides_that_fail(tmp_path, monkeypatch):
    """Run 87a6f1f8: one 45 s timeout in Week 2 used to switch off the screenshot review of every later slide."""
    import subprocess
    slide_render = _fresh_renderer(monkeypatch)
    outcomes, soffice = iter(["ok", "hang", "ok", "hang", "hang", "hang", "ok"]), []

    def run(cmd, **kwargs):
        if cmd[0] == "pdftoppm":
            (tmp_path / "slide-1.png").write_bytes(b"png")
            return
        soffice.append((cmd[1], kwargs["timeout"]))
        if next(outcomes) == "hang":
            raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    monkeypatch.setattr(slide_render.subprocess, "run", run)
    render = lambda: slide_render.render_deck_pngs(str(tmp_path / "d.pptx"), str(tmp_path))
    png = [str(tmp_path / "slide-1.png")]
    assert [render() for _ in range(3)] == [png, [], png]  # the failed slide alone loses its screenshot
    # the render after a failure gets a fresh profile, so it has the cold-start timeout
    assert soffice[2][0] != soffice[1][0] and soffice[2][1] == slide_render.FIRST_SOFFICE_TIMEOUT_S
    assert [render() for _ in range(4)] == [[], [], [], []]  # 3 failures in a row give up for the run
    assert len(soffice) == 6 and slide_render._disabled_reason


def test_screenshot_renders_only_the_newest_slide(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from pptx import Presentation
    from digitalagedu.core.llm import presentation_designer as pd
    monkeypatch.chdir(tmp_path)
    rendered = []

    def fake_render(deck, out_dir):
        rendered.append([s.shapes.title.text for s in Presentation(deck).slides])
        png = os.path.join(out_dir, "slide-1.png")
        open(png, "wb").close()
        return [png]

    monkeypatch.setattr(pd, "render_deck_pngs", fake_render)
    prs = Presentation()
    for title in ("one", "two", "three"):
        prs.slides.add_slide(prs.slide_layouts[0]).shapes.title.text = title
    repl = SimpleNamespace(prs=prs, output_path=str(tmp_path / "deck.pptx"))
    designer = pd.PresentationDesigner(client=None)
    first, second = designer._screenshot_last_slide(repl, "s3"), designer._screenshot_last_slide(repl, "s3")
    assert rendered == [["three"], ["three"]] and len(prs.slides) == 3  # the live deck is untouched
    assert first != second and os.path.exists(first) and os.path.exists(second)


def test_text_that_does_not_fit_grows_its_box_and_is_never_cut():
    """Run ee09eaac: '…' cut ~43 lines a deck, and metric cards squeezed into 0.45 in stacked their text."""
    from pptx.util import Inches
    from digitalagedu.core.llm.slide_kit.theme import GROWN_TEXT, layout_issues
    prs = Presentation()
    slide = slide_kit.create_slide(prs)
    card = slide_kit.add_metric_card(slide, 0.55, 6.6, 3.9, 0.45, label="Phase-1 overall accuracy", value="91.8%", subtext="this run")
    text = next(s for s in slide.shapes if s.has_text_frame and "91.8%" in s.text_frame.text)
    assert text.name == GROWN_TEXT and "…" not in text.text_frame.text
    assert card.top + card.height >= text.top + text.height > Inches(7.1)  # the card grew with its text
    issues = layout_issues(slide)
    assert len(issues) == 1 and "runs off" in issues[0] and "grown to fit its text, do not shrink it" in issues[0]

    long_body = "Recall means: of all images that truly belong to a class, the share the model found. " * 6
    slide = slide_kit.create_slide(prs)
    slide_kit.add_card(slide, 0.5, 1.8, 4.0, 1.2, title="In plain words", body=long_body)
    assert any(s.has_text_frame and s.text_frame.text.endswith(long_body) for s in slide.shapes)  # every word kept


def test_layout_issues_flags_shapes_stacked_on_a_text_box_text(tmp_path):
    """Run ee09eaac (Week 2, slide 2): images and captions were placed inside the explanation's text box."""
    import matplotlib.pyplot as plt
    from pptx.util import Inches, Pt
    from digitalagedu.core.llm.slide_kit.theme import layout_issues
    png = str(tmp_path / "leaf.png")
    plt.imsave(png, [[0.0, 1.0]])
    prs = Presentation()

    def text_box(slide, y, h, text):
        box = slide.shapes.add_textbox(Inches(9.2), Inches(y), Inches(3.4), Inches(h))
        box.text_frame.word_wrap = True
        box.text_frame.text = text
        box.text_frame.paragraphs[0].font.size = Pt(12)

    stacked = slide_kit.create_slide(prs)
    text_box(stacked, 1.95, 3.2, "In plain words: " + "each leaf photo becomes numbers the model can compare. " * 5)
    stacked.shapes.add_picture(png, Inches(9.46), Inches(2.15), Inches(1.2), Inches(1.2))
    issues = layout_issues(stacked)
    assert len(issues) == 1 and "sits on the text of 'In plain words" in issues[0]

    labelled = slide_kit.create_slide(prs)  # slide_kit's artifact comparison: a one-line label above its image
    text_box(labelled, 4.6, 2.35, "ORIGINAL INPUT")
    labelled.shapes.add_picture(png, Inches(9.3), Inches(5.05), Inches(1.7), Inches(1.7))
    assert layout_issues(labelled) == []


def test_over_long_planned_text_is_rewritten_never_cut():
    """Run ee09eaac: the planner wrote 450-650 characters for 320-character boxes; cutting them showed '…'."""
    from unittest.mock import MagicMock
    from digitalagedu.core.llm.presentation_designer import PresentationDesigner
    from digitalagedu.core.llm.presentation_prompts import ShortenedTexts
    plan = _lesson_plan()
    long_explanation, long_point = "A plain-language explanation. " * 20, "A key point that runs on and on. " * 5
    plan.slides[2].explanation, plan.slides[3].on_slide_text[1] = long_explanation, long_point
    client = MagicMock()
    client.chat.completions.create.return_value = ShortenedTexts(texts=["A short explanation.", long_point[:150] + "..."])
    PresentationDesigner(client=client)._shorten_texts(plan)
    sent = client.chat.completions.create.call_args.kwargs["messages"][1]["content"]
    assert "1. (at most 320 characters" in sent and "2. (at most 110 characters" in sent
    assert plan.slides[2].explanation == "A short explanation."
    assert plan.slides[3].on_slide_text[1] == long_point  # a rewrite ending in '...' is refused: kept whole

    client.chat.completions.create.side_effect = RuntimeError("LLM down")
    plan.slides[2].explanation = long_explanation
    PresentationDesigner(client=client)._shorten_texts(plan)
    assert plan.slides[2].explanation == long_explanation  # a failed call keeps the text whole


def test_crowded_slide_is_split_into_two_or_kept_whole(tmp_path, monkeypatch):
    """When a slide still overlaps after its reviews, its content is rebuilt as two slides instead of cut."""
    from unittest.mock import MagicMock
    from digitalagedu.core.llm.presentation_designer import PresentationDesigner
    from digitalagedu.core.llm.presentation_prompts import EvidenceItem, SlideSplit
    plan = _lesson_plan()
    spec = plan.slides[-1]  # application slide with code
    first = spec.model_copy(update={"title": "Part one", "code_function": None})
    second = spec.model_copy(update={"title": "Part two", "code_function": "compute_iou", "evidence": [
        EvidenceItem(label="Accuracy", value="94.5%", context="this run"),
        EvidenceItem(label="Invented", value="99.9%", context="not in the slide")]})
    client = MagicMock()
    client.chat.completions.create.return_value = SlideSplit(first=first, second=second)
    designer = PresentationDesigner(client=client)
    halves = designer._split_slide(spec)
    assert [h.evidence[0].value for h in halves] == ["94.5%", "94.5%"] and len(halves[1].evidence) == 1  # invented dropped
    assert [h.code_function for h in halves] == [None, spec.code_function]  # the verified code appears once

    monkeypatch.setattr(designer, "_split_slide", lambda s: halves)
    monkeypatch.setattr(designer, "_get_matching_recipe", lambda *a: "")

    def deck_after_split(fail_part=None):
        repl = SlideDeckRepl(str(tmp_path / "deck.pptx"), {}, "", str(tmp_path))
        crowded = slide_kit.create_slide(repl.prs)
        crowded.shapes.add_textbox(0, 0, 100, 100).text_frame.text = "crowded original"

        def build(repl_, system, prompt, label, **kw):
            if fail_part and f"{fail_part} (" in label:
                raise RuntimeError("could not build")
            slide_kit.create_slide(repl_.prs).shapes.add_textbox(0, 0, 100, 100).text_frame.text = label
            return True

        monkeypatch.setattr(designer, "_build_slide", build)
        designer._replace_with_split(repl, spec, plan, 10, "def compute_iou(a, b):\n    return 1\n", {}, None, [])
        return [" ".join(sh.text_frame.text for sh in s.shapes if sh.has_text_frame).strip() for s in repl.prs.slides]

    assert deck_after_split() == ["Slide 10a ('Part one')", "Slide 10b ('Part two')"]
    assert deck_after_split(fail_part="10b") == ["crowded original"]  # never lose content: the original stays


def test_slides_added_after_a_drop_get_unique_part_names(tmp_path):
    """Run 87a6f1f8: after a split dropped its crowded original, the next slide reused a taken name and the saved
    decks held two ppt/slides/slide15.xml (PowerPoint repairs such a file and may keep the wrong copy)."""
    import collections
    import zipfile
    from pptx import Presentation
    import re
    repl = SlideDeckRepl(str(tmp_path / "deck.pptx"), {}, "", str(tmp_path))
    for text in ["one", "crowded", "half a", "half b", "failed retry"]:
        slide = slide_kit.create_slide(repl.prs)
        slide.shapes.add_textbox(0, 0, 100, 100).text_frame.text = text
        slide.notes_slide.notes_text_frame.text = f"notes {text}"
        repl.prs.save(str(tmp_path / "review.pptx"))  # the screenshot review saves after every slide (run e5422bbc)
    repl._drop_slide(1)  # a split replaced the crowded slide
    repl._drop_slides_from(3)  # a failed snippet's half-built slide
    for text in ["next", "takeaways"]:
        slide_kit.create_slide(repl.prs).shapes.add_textbox(0, 0, 100, 100).text_frame.text = text
    repl.prs.save(str(tmp_path / "deck.pptx"))
    names = zipfile.ZipFile(tmp_path / "deck.pptx").namelist()
    assert [n for n, c in collections.Counter(names).items() if c > 1] == []
    # Every slide part is referenced exactly once, and each notes page points back to its own slide
    deck = zipfile.ZipFile(tmp_path / "deck.pptx")
    targets = re.findall(r'Target="(slides/slide\d+\.xml)"', deck.read("ppt/_rels/presentation.xml.rels").decode())
    assert sorted(targets) == sorted(n.removeprefix("ppt/") for n in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", n))
    for slide_name in targets:
        notes = re.findall(r'Target="\.\./notesSlides/(notesSlide\d+\.xml)"',
                           deck.read(f"ppt/slides/_rels/{slide_name.split('/')[1]}.rels").decode())
        for note in notes:
            back = re.findall(r'Target="\.\./(slides/slide\d+\.xml)"', deck.read(f"ppt/notesSlides/_rels/{note}.rels").decode())
            assert back == [slide_name], (note, back, slide_name)
    saved = Presentation(str(tmp_path / "deck.pptx"))
    assert [" ".join(sh.text_frame.text for sh in s.shapes if sh.has_text_frame).strip() for s in saved.slides] == [
        "one", "half a", "half b", "next", "takeaways"]
