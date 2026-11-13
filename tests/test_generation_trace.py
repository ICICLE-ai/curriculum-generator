"""PROV generation trace + sandbox failure attribution."""
import hashlib
import json

from digitalagedu.core.llm.generation_trace import GenerationTrace, attribute_failures

# Trimmed from the 2026-10-26 cluster run, where every repair went to the coder although 4 errors were in the tests
CLUSTER_LOG = '''EFE.EFE.E
======================================================================
ERROR: test_ImageProcessor (__main__.TestAgriculturalImagingSubsystem.test_ImageProcessor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/tmpfju7bdlo/test_runner.py", line 47, in test_ImageProcessor
    image_path = df['image_path'].iloc[0]
                 ^^
NameError: name 'df' is not defined

======================================================================
ERROR: test_run_pipeline (__main__.TestAgriculturalImagingSubsystem.test_run_pipeline)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/opt/conda/lib/python3.11/site-packages/PIL/Image.py", line 2811, in getchannel
    channel = self.getbands().index(channel)
ValueError: tuple.index(x): x not in tuple

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/tmp/tmpfju7bdlo/test_runner.py", line 93, in test_run_pipeline
    results = run_pipeline()
  File "/tmp/tmpfju7bdlo/leaf_image_exploration_solution.py", line 20, in color_channel_histograms
    histograms = {channel: np.histogram(image.getchannel(channel), bins=256)[0] for channel in channels}
  File "/opt/conda/lib/python3.11/site-packages/PIL/Image.py", line 2814, in getchannel
    raise ValueError(msg) from e
ValueError: The image has no channel "red"

======================================================================
FAIL: test_error_analysis (__main__.TestAgriculturalImagingSubsystem.test_error_analysis)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/tmpfju7bdlo/test_runner.py", line 88, in test_error_analysis
    self.assertIsInstance(error_analysis_results, dict)
AssertionError: [{'class': 0}] is not an instance of <class 'dict'>

----------------------------------------------------------------------
Ran 9 tests in 0.082s

FAILED (failures=1, errors=2)'''


def test_attribution_blames_the_file_of_the_deepest_frame():
    failures = attribute_failures(CLUSTER_LOG, contract_names=["run_pipeline"])
    assert [(f["test"], f["blame"], f["file"], f["line"]) for f in failures] == [
        ("test_ImageProcessor", "test", "test_runner.py", 47),
        ("test_run_pipeline", "solution", "leaf_image_exploration_solution.py", 20),
        ("test_error_analysis", "contract_mismatch", "test_runner.py", 88),
    ]
    assert failures[1]["exception"] == 'ValueError: The image has no channel "red"'
    assert [f["kind"] for f in failures] == ["test_error", "solution_error", "contract_mismatch"]


def test_issue_kinds_for_fixtures_packages_and_timeouts():
    frame = '  File "/tmp/x/m_solution.py", line 3, in <module>\n'
    kind = lambda exc, names=(): attribute_failures(f"Traceback (most recent call last):\n{frame}{exc}", names)[0]["kind"]
    assert kind("FileNotFoundError: [Errno 2] No such file or directory: 'fixtures/results.csv'") == "missing_fixture"
    assert kind("ModuleNotFoundError: No module named 'tensorflow'") == "missing_package"
    assert attribute_failures("Execution timed out after 120 seconds")[0]["kind"] == "timeout"


def test_missing_contract_symbol_is_the_solutions_fault():
    log = ('Traceback (most recent call last):\n  File "/tmp/x/test_runner.py", line 4, in <module>\n'
           "    run_pipeline()\nNameError: name 'run_pipeline' is not defined")
    assert attribute_failures(log, ["run_pipeline"])[0]["blame"] == "solution"
    assert attribute_failures(log, [])[0]["blame"] == "test"
    assert attribute_failures("Execution timed out after 120 seconds")[0]["blame"] == "environment"


def test_trace_entities_are_hashed_files_and_manifest_files_are_checked(tmp_path):
    fixture = tmp_path / "results.csv"
    fixture.write_text("a,b\n1,2\n", encoding="utf-8")
    manifest = [{"artifact_id": "artifact_run_7_results_csv", "name": "results.csv",
                 "sha256": hashlib.sha256(fixture.read_bytes()).hexdigest()}]
    trace = GenerationTrace(str(tmp_path), "m-1", "qwen", workflow_run_id="run_7", manifest=manifest)

    v1 = trace.add_entity("solution", "x = 1\n", ext="py", versioned=True, compiles=True)
    v2 = trace.add_entity("solution", "x = 2\n", ext="py", versioned=True, compiles=True)
    act = trace.add_activity("llm_call", "agent1_coder", purpose="repair")
    trace.relate("wasDerivedFrom", generatedEntity=v2, usedEntity=v1)
    trace.relate("used", activity=act, entity=trace.file(str(fixture)))
    doc = json.loads(open(trace.save(), encoding="utf-8").read())

    assert (v1, v2, trace.latest["solution"]) == ("dage:solution_v1", "dage:solution_v2", "dage:solution_v2")
    assert (tmp_path / doc["entity"][v2]["dage:path"]).read_text() == "x = 2\n"
    assert doc["entity"]["dage:artifact_artifact_run_7_results_csv"]["dage:matches_manifest_sha256"] is True
    assert doc["agent"]["dage:agent1_coder"]["dage:model"] == "qwen"
    ids = set(doc["entity"]) | set(doc["activity"]) | set(doc["agent"])
    for relation in ("used", "wasDerivedFrom", "wasAssociatedWith"):
        for record in doc[relation].values():
            assert set(record.values()) <= ids
