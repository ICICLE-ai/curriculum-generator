"""Phase 2 rerun from a finished run: staging Phase 1 outputs, the config lock, and keeping finished weeks."""
import json
import os

import pytest

import run_pipeline
from digitalagedu.core.artifact_validator import compute_file_sha256
from digitalagedu.core.llm import lineage, week_builder
from digitalagedu.core.llm.schemas.module_types import Module

OUT = "outputs/run_v1"


def _write(path, text="x"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _week(ex_dir, week, mid, verified):
    d = os.path.join(ex_dir, f"Week_{week:02d}", mid)
    _write(os.path.join(d, f"{mid}_verification.json"), json.dumps({"verified": verified}))
    _write(os.path.join(d, f"{mid}_presentation.pptx"))
    _write(os.path.join(d, f"{mid}_manifest.json"), json.dumps({"source_artifacts": ["results.csv"]}))
    _write(os.path.join(d, "trace", "problem_formulation_v2.json"), json.dumps({
        "suggested_focus": "arrays", "milestone_subsystems": [{"components": [{"name": "load_images"}]}]}))
    return d


@pytest.fixture
def finished_run(tmp_path):
    """A job dir with Phase 1 outputs, a passed week 1 and a failed week 2, plus the config it ran with."""
    config = tmp_path / "config.yaml"
    config.write_text("output:\n  directory: ./outputs/run_v1\n")
    src = tmp_path / "job_a"
    out = src / OUT
    for name in ("results.csv", "run_summary.json"):
        _write(str(out / name))
    _write(str(out / "provenance.json"), json.dumps({"configuration_hash": compute_file_sha256(str(config))}))
    _write(str(src / "models" / "head.pth"))
    _write(str(src / "tapisjob.sh"))
    ex = str(out / "exercises")
    _write(os.path.join(ex, "syllabus_plan.json"), "{}")
    _week(ex, 1, "numpy_basics", verified=True)
    _week(ex, 2, "pandas_stats", verified=False)
    return src, config, tmp_path / "job_b"


def test_failed_mode_copies_phase1_and_only_finished_weeks(finished_run):
    src, config, dest = finished_run
    kept = run_pipeline.stage_phase2_rerun(str(src), "./outputs/run_v1", str(config), "failed", str(dest))
    ex = dest / OUT / "exercises"
    assert kept == [os.path.join("Week_01", "numpy_basics")]
    assert (dest / OUT / "results.csv").is_file() and (dest / "models" / "head.pth").is_file()
    assert (ex / "syllabus_plan.json").is_file() and (ex / "Week_01" / "numpy_basics").is_dir()
    assert not (ex / "Week_02").exists()
    assert not (dest / "tapisjob.sh").exists()  # the old job's launch files stay behind


def test_all_mode_copies_no_exercises(finished_run):
    src, config, dest = finished_run
    assert run_pipeline.stage_phase2_rerun(str(src), "./outputs/run_v1", str(config), "all", str(dest)) == []
    assert (dest / OUT / "results.csv").is_file()
    assert not (dest / OUT / "exercises").exists()


def test_changed_config_is_locked_out(finished_run):
    src, config, dest = finished_run
    config.write_text(config.read_text() + "# edited\n")
    with pytest.raises(RuntimeError, match="locked to the original config"):
        run_pipeline.stage_phase2_rerun(str(src), "./outputs/run_v1", str(config), "failed", str(dest))
    assert not dest.exists()


def test_unfinished_phase1_is_rejected(finished_run):
    src, config, dest = finished_run
    os.remove(src / OUT / "results.csv")
    with pytest.raises(RuntimeError, match="Phase 1 didn't finish"):
        run_pipeline.stage_phase2_rerun(str(src), "./outputs/run_v1", str(config), "failed", str(dest))


def test_finished_week_result_reads_saved_lineage(tmp_path):
    d = _week(str(tmp_path), 1, "numpy_basics", verified=True)
    _write(os.path.join(d, "numpy_basics_generation_trace.json"), "{}")
    module = Module(id="numpy_basics", title="NumPy", week=1, context="c", difficulty="intro", level="UG")
    result = week_builder.finished_week(module, d)
    assert result.ok and result.error is None
    assert result.source_arts == ["results.csv"]
    assert result.trace.endswith("numpy_basics_generation_trace.json")


def test_one_matching_rule_for_binding_and_reconciling(tmp_path):
    """A week bound to an artifact id is linked to exactly that artifact, not to every artifact whose slug or file
    name happens to contain it (the old reconcile matched substrings)."""
    manifest = [{"artifact_id": "mask", "name": "mask.png"},
                {"artifact_id": "mask_inverted", "name": "mask_inverted_display.png"}]
    assert lineage.names_artifact("MASK", manifest[0]) and lineage.names_artifact("mask.png", manifest[0])
    assert not lineage.names_artifact("mask", manifest[1])
    (tmp_path / "provenance.json").write_text(json.dumps({"artifact_manifest": manifest}))
    lineage.reconcile_module_bindings(str(tmp_path), {"week_1": ["mask"]})
    linked = json.loads((tmp_path / "provenance.json").read_text())["artifact_manifest"]
    assert [a.get("module_references") for a in linked] == [["week_1"], None]
    with pytest.raises(ValueError, match="unresolvable"):
        lineage.reconcile_module_bindings(str(tmp_path), {"week_2": ["no_such_artifact"]})


def test_content_bank_stages_from_output_dir_with_new_config(finished_run, tmp_path):
    src, _old_config, dest = finished_run
    new_config = tmp_path / "new_curriculum.yaml"
    new_config.write_text("output:\n  directory: ./outputs/new_grade_level\n")
    new_hash = compute_file_sha256(str(new_config))

    kept = run_pipeline.stage_phase2_rerun(
        str(src / OUT), "./outputs/new_grade_level", str(new_config), "failed", str(dest), unlock_config=True
    )
    assert kept == []
    new_out = dest / "outputs" / "new_grade_level"
    assert (new_out / "results.csv").is_file()
    assert (dest / "models" / "head.pth").is_file()
    assert not (new_out / "exercises").exists()

    prov = json.loads((new_out / "provenance.json").read_text(encoding="utf-8"))
    assert prov["configuration_hash"] == new_hash
    assert prov["source_bank_dir"] == os.path.abspath(str(src / OUT))
    assert "source_configuration_hash" in prov


def test_content_bank_resolves_job_root_when_output_dir_differs(finished_run, tmp_path):
    src, _old_config, dest = finished_run
    new_config = tmp_path / "new_curriculum.yaml"
    new_config.write_text("output:\n  directory: ./outputs/custom_bank_run\n")

    run_pipeline.stage_phase2_rerun(
        str(src), "./outputs/custom_bank_run", str(new_config), "all", str(dest), unlock_config=True
    )
    assert (dest / "outputs" / "custom_bank_run" / "results.csv").is_file()
    assert (dest / "models" / "head.pth").is_file()
    assert not (dest / "outputs" / "custom_bank_run" / "exercises").exists()


def test_content_bank_resolves_flat_archive_subdir(tmp_path):
    """Tapis archiving when execSystemOutputDir=/jobs/${JobUUID}/outputs stores <run_name>/... directly."""
    archive = tmp_path / "smart_curriculum_designer_archives" / "curriculum-run-1234"
    _write(str(archive / "run_v1" / "results.csv"))
    _write(str(archive / "run_v1" / "run_summary.json"))
    _write(str(archive / "run_v1" / "provenance.json"), json.dumps({"configuration_hash": "oldhash"}))
    _write(str(archive / "run_v1" / "exercises" / "Week_01" / "m" / "m_verification.json"), "{}")

    new_config = tmp_path / "new_curriculum.yaml"
    new_config.write_text("output:\n  directory: ./outputs/fresh_bank_run\n")
    dest = tmp_path / "job_c"

    run_pipeline.stage_phase2_rerun(
        str(archive), "./outputs/fresh_bank_run", str(new_config), "failed", str(dest), unlock_config=True
    )
    new_out = dest / "outputs" / "fresh_bank_run"
    assert (new_out / "results.csv").is_file()
    assert not (new_out / "exercises").exists()
    prov = json.loads((new_out / "provenance.json").read_text(encoding="utf-8"))
    assert prov["configuration_hash"] == compute_file_sha256(str(new_config))
    assert prov["source_configuration_hash"] == "oldhash"
    assert prov["source_bank_dir"] == os.path.abspath(str(archive / "run_v1"))
