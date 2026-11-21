"""Builds one curriculum week after its Stage A problem statement: tests, verified solution, starter code and deck.

Interface: build_week(run, module, formulation, history) -> WeekResult, plus finished_week() for a week a Phase 2
rerun kept, and init_worker() for spawned week processes. Everything a week needs arrives in the WeekRun.
"""
import contextlib
import dataclasses
import json
import os
import re
import sys
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from digitalagedu.core.writer import write_file
from digitalagedu.core.llm.schemas import Module, ProblemStatementSchema, ValidatedExerciseSchema
from digitalagedu.core.llm import ai_setup
from digitalagedu.core.llm.ai_setup import get_instructor_client, get_openai_client, ask_code
from digitalagedu.core.llm.telemetry import formulate_problem_statement
from digitalagedu.core.llm.context import (
    build_system_prompt,
    build_exercise_prompt,
    build_scaffold_prompt,
    build_qa_prompt,
    build_presentation_payload,
)
from digitalagedu.core.llm.sandbox import clean_code_snippet
from digitalagedu.core.llm.presentation_designer import PresentationDesigner
from digitalagedu.core.llm.generation_trace import GenerationTrace, condense_log
from digitalagedu.core.llm.self_healing import ContractRevisionNeeded, verify_with_self_healing
from digitalagedu.core.llm import gates, lineage

MAX_CONTRACT_REVISIONS = 1


@dataclass(frozen=True)
class WeekRun:
    """The run-wide inputs every week reads. Picklable once the clients are stripped (for_worker); a spawned
    worker builds its own clients from base_url and api_key, so the key never goes back into os.environ."""
    models: Any
    root_config: Any
    config_path: str
    telemetry: Dict[str, Any]
    telemetry_dir: Optional[str]
    output_dir: str
    known_manifest: List[Dict[str, Any]]
    artifact_source_dirs: List[str]
    fixture_note: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    client: Any = None
    code_client: Any = None

    def for_worker(self) -> "WeekRun":
        return dataclasses.replace(self, client=None, code_client=None)

    def with_clients(self) -> "WeekRun":
        if self.client is not None:
            return self
        return dataclasses.replace(self, client=get_instructor_client(base_url=self.base_url, api_key=self.api_key),
                                   code_client=get_openai_client(base_url=self.base_url, api_key=self.api_key))


@dataclass
class WeekResult:
    module_id: str
    week: int
    ok: bool = False
    error: Optional[str] = None
    source_arts: List[str] = field(default_factory=list)
    trace: Optional[str] = None
    log: Optional[str] = None
    minutes: float = 0.0


def init_worker(model_slots: Dict[str, Any]) -> None:
    """Start-up of a spawned week worker: the parent's per-model caps, shared by every worker."""
    ai_setup.MODEL_SLOTS.update(model_slots)


def module_dir(output_dir: str, module: Module) -> str:
    return os.path.join(output_dir, f"Week_{module.week:02d}", module.id.replace("-", "_"))


def finished_week(module: Module, week_dir: str) -> WeekResult:
    """The result for a week a Phase 2 rerun copied over finished, read from its saved manifest and trace."""
    clean_id = os.path.basename(week_dir)
    out = lambda suffix: os.path.join(week_dir, f"{clean_id}_{suffix}")
    trace = out("generation_trace.json")
    return WeekResult(module.id, module.week, ok=True, source_arts=lineage.manifest_sources(out("manifest.json")),
                      trace=trace if os.path.isfile(trace) else None, log=out("phase2.log"))


def collect_deck_artifacts(telemetry_dir: Optional[str], telemetry: Dict[str, Any]) -> Dict[str, str]:
    """Authentic pipeline fixtures (raw/mask samples, contrastive pair) offered to the slide builder."""
    artifacts = {}
    if telemetry_dir:
        raw = _first_image(os.path.join(telemetry_dir, "images", "raw"))
        mask = _first_image(os.path.join(telemetry_dir, "images", "masks"))
        if raw:
            artifacts["raw_sample"] = raw
        if mask:
            artifacts["mask_sample"] = mask
        # Real run data for slide charts (slides must never plot simulated data)
        for key, name in (("results_csv", "results.csv"), ("confusion_matrix", "eval_confusion_matrix.png")):
            if os.path.isfile(os.path.join(telemetry_dir, name)):
                artifacts[key] = os.path.join(telemetry_dir, name)
    contrastive = telemetry.get("contrastive_samples", {}) if telemetry else {}
    for key in ("top_success", "hard_failure"):
        if (contrastive.get(key) or {}).get("image_path"):
            artifacts[key] = str(contrastive[key]["image_path"])
    return artifacts


def _first_image(folder: Optional[str]) -> Optional[str]:
    if folder and os.path.isdir(folder):
        return next((os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith((".jpg", ".png", ".jpeg"))), None)
    return None


def _ask_code(code_client, model_name: str, prompt: str, what: str, max_retries: int = 2, **trace_kwargs) -> str:
    """Fenced-code LLM call (see ask_code) with the shared curriculum system prompt."""
    return ask_code(code_client, model_name, [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": prompt}
    ], what, max_retries=max_retries, **trace_kwargs)


def _write_code_file(path: str, docstring: str, code: str):
    write_file(path, lambda f: f.write(f'"""\n{docstring}\n"""\n\n{clean_code_snippet(code)}\n'))


@contextlib.contextmanager
def _week_log(path: str):
    """Sends a week's output to its own log: Python prints through sys.stdout/stderr, and subprocess or
    library writes through file descriptors 1 and 2 (restored afterwards for weeks run inline)."""
    sys.stdout.flush()
    sys.stderr.flush()
    saved = os.dup(1), os.dup(2)
    log = open(path, "a", encoding="utf-8", buffering=1)
    try:
        os.dup2(log.fileno(), 1)
        os.dup2(log.fileno(), 2)
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            yield
    finally:
        log.flush()
        os.dup2(saved[0], 1)
        os.dup2(saved[1], 2)
        for fd in saved:
            os.close(fd)
        log.close()


def build_week(run: WeekRun, module: Module, prepared_formulation: Optional[ProblemStatementSchema],
               curriculum_history: List[Dict[str, Any]]) -> WeekResult:
    """Builds one week after its Stage A problem statement. Never raises: a failure is reported in the result."""
    run = run.with_clients()
    client, code_client, models, telemetry = run.client, run.code_client, run.models, run.telemetry
    fixture_note = run.fixture_note

    clean_id = module.id.replace("-", "_")
    week_dir = module_dir(run.output_dir, module)
    os.makedirs(week_dir, exist_ok=True)
    out = lambda suffix: os.path.join(week_dir, f"{clean_id}_{suffix}")
    result = WeekResult(module.id, module.week, log=out("phase2.log"))
    started = time.monotonic()

    with _week_log(result.log):
        print(f"\n==================================================")
        print(f"Processing LLM Module: {module.title} (Week {module.week})...")
        print(f"==================================================")
        trace = GenerationTrace(
            week_dir, module.id, models.coder,
            workflow_run_id=telemetry.get("provenance", {}).get("workflow_run_id"), manifest=run.known_manifest
        )
        gates.configure(getattr(getattr(run.root_config, "execution", None), "quality_gates", "log"))
        presentation_designer = PresentationDesigner(client=client, model_name=models.slides, code_client=code_client,
                                                     reviewer_model=models.slide_reviewer, plan_model=models.planner)
        try:
            # Steps 0-3 rerun once with a revised contract if the Arbiter rules the contract at fault
            revision_feedback, revision_verdict, escalations, failure_reason = None, None, [], ""
            for revision in range(1 + MAX_CONTRACT_REVISIONS):
                # 0. Agent 0: Problem Formulation with Subsystem Contracts & Cumulative Memory (first one from Stage A)
                if revision == 0 and prepared_formulation is not None:
                    problem_formulation = prepared_formulation
                else:
                    print(f"0. Agent 0: {'Revising' if revision else 'Formulating'} problem statement & subsystem contracts ({module.id})...")
                    problem_formulation = formulate_problem_statement(
                        module=module,
                        telemetry=telemetry,
                        client=client,
                        model_name=models.planner,
                        curriculum_history=curriculum_history,
                        revision_feedback=revision_feedback,
                        fixture_note=fixture_note
                    )

                source_arts = lineage.resolve_source_artifacts(problem_formulation, run.known_manifest, module, clean_id)
                overview_content = problem_formulation.markdown_overview or f"# {problem_formulation.title}\n\n{problem_formulation.problem_statement}"
                if source_arts:
                    overview_content += "\n\n## Workflow Evidence & Artifact Lineage\n"
                    overview_content += "This laboratory module is grounded in validated research workflow artifacts from the computational pipeline:\n"
                    overview_content += "".join(f"- **Source Artifact ID:** `{sa}`\n" for sa in source_arts)
                write_file(out("overview.md"), lambda f: f.write(overview_content))
                print(f"  -> Saved Student Overview: {out('overview.md')}")

                lineage.write_module_manifest(out("manifest.json"), module, source_arts, telemetry, run.root_config,
                                              run.config_path)
                result.source_arts = source_arts

                # Trace: Agent 0's contract, derived from the Phase 1 artifacts it was bound to (and the verdict on a revision)
                previous_formulation = trace.latest.get("problem_formulation")
                formulation_entity = trace.add_entity("problem_formulation", problem_formulation.model_dump_json(indent=2),
                                                      ext="json", versioned=True)
                trace.relate("wasAttributedTo", entity=formulation_entity, agent=trace.agent("agent0_director"))
                for source in ([previous_formulation, revision_verdict] if revision else []):
                    trace.relate("wasDerivedFrom", generatedEntity=formulation_entity, usedEntity=source)
                for art in run.known_manifest:
                    art_path = os.path.join(run.telemetry_dir or "", str(art.get("artifact_path", "")))
                    if art.get("artifact_id") in source_arts and os.path.isfile(art_path):
                        trace.relate("wasDerivedFrom", generatedEntity=formulation_entity, usedEntity=trace.file(art_path))
                with open(out("manifest.json"), "r", encoding="utf-8") as f:
                    manifest_entity = trace.add_entity("module_manifest", f.read(), ext="json")
                trace.relate("wasDerivedFrom", generatedEntity=manifest_entity, usedEntity=formulation_entity)
                gates.run_gate("G1 contract", lambda: gates.contract_gate(problem_formulation), trace)

                # 1. Agent 2 (QA): TDD Step 1 - Generate Unit Tests First from Subsystem Contracts
                print(f"1. Agent 2 (QA): Writing property-based unit tests for {module.id}...")
                qa_prompt = build_qa_prompt(module, problem_formulation=problem_formulation, telemetry=telemetry) + fixture_note
                unit_test = _ask_code(code_client, models.coder, qa_prompt, "unit test file", max_retries=3,
                                      trace=trace, agent="agent2_qa", artifact="unit_test", used=[formulation_entity])
                gates.run_gate("G2 tests", lambda: gates.tests_gate(unit_test, problem_formulation), trace)

                # 2. Agent 1 (Coder): TDD Step 2 - Implement Reference Solution to Pass Unit Tests
                print(f"2. Agent 1 (Coder): Synthesizing reference solution satisfying unit tests ({module.id})...")
                exercise_prompt = build_exercise_prompt(
                    module=module,
                    problem_formulation=problem_formulation,
                    unit_test_code=unit_test,
                    curriculum_history=curriculum_history,
                    telemetry=telemetry
                ) + fixture_note
                solution_code = _ask_code(code_client, models.coder, exercise_prompt, "reference solution", max_retries=3,
                                          trace=trace, agent="agent1_coder", artifact="solution",
                                          used=[formulation_entity, trace.latest["unit_test"]])

                # 3. Execution Sandbox Verification with escalating self-healing (see self_healing.py)
                print(f"3. Sandbox: Verifying solution against unit tests ({module.id})...")
                try:
                    success, log, failures, round_escalations, unit_test, solution_code = verify_with_self_healing(
                        client, code_client, models.coder, module, problem_formulation, qa_prompt, exercise_prompt,
                        unit_test, solution_code, run.artifact_source_dirs, trace, fixture_note,
                        arbiter_model=models.arbiter,
                    )
                    escalations += round_escalations
                    break
                except ContractRevisionNeeded as needed:
                    escalations += needed.escalations
                    success, log, failures = False, needed.log, needed.failures
                    failure_reason = (f" Unresolved after {revision} contract revision(s); "
                                      f"last Arbiter verdict ({needed.verdict.fault}): {needed.verdict.rationale}")
                    revision_feedback, revision_verdict = needed.feedback(), needed.verdict_entity
                    if revision < MAX_CONTRACT_REVISIONS:
                        print(f"  -> Contract revision requested by the Arbiter: {needed.verdict.rationale}")

            if not success:
                print(f"  -> Final Sandbox Verification Log (failures only; full log in verification.json):\n{condense_log(log)}")
            write_file(out("verification.json"), lambda f: json.dump({
                "module_id": module.id,
                "verified": success,
                "failures": failures,
                "escalations": escalations,
                "trace": os.path.basename(trace.path()),
                "log": "All tests passed cleanly in sandbox." if success else log
            }, f, indent=2))
            # Slides must never be built from an unverified solution.
            if not success:
                raise RuntimeError(f"Sandbox verification failed for module '{module.id}'.{failure_reason} See {out('verification.json')}")
            # Repairs rewrite tests, so the shipped (verified) file is checked again
            gates.run_gate("G2 tests (verified)", lambda: gates.tests_gate(unit_test, problem_formulation), trace)

            # 4. TDD Step 3: Exercise Scaffolding derived from verified solution
            print(f"4. Scaffolding student starter code from verified solution ({module.id})...")
            starter_code = None
            try:
                scaffold_prompt = build_scaffold_prompt(module, problem_formulation, solution_code)
                starter_result = _ask_code(code_client, models.coder, scaffold_prompt, "student starter code",
                                           trace=trace, agent="agent1_coder", artifact="starter_code",
                                           used=[trace.latest["solution"]])
                if len(starter_result) > 30:
                    starter_code = starter_result
            except Exception as e:
                print(f"  -> Notice: Fallback to existing starter scaffolding: {e}")

            exercise = ValidatedExerciseSchema(
                title=problem_formulation.title,
                instructions=problem_formulation.problem_statement,
                starter_code=starter_code or "# Student implementation starter skeleton\n",
                solution_code=solution_code,
                # Every test passed against the solution, so the shipped tests check the student's exercise instead
                # (the trace keeps the verified _solution version)
                unit_test=re.sub(rf"\b{clean_id}_solution\b", f"{clean_id}_exercise", unit_test)
            )
            write_file(out("generated.json"), lambda f: json.dump(exercise.model_dump(), f, indent=2))
            _write_code_file(out("exercise.py"), f"{exercise.title}\n\nInstructions:\n{exercise.instructions}", exercise.starter_code)
            _write_code_file(out("solution.py"), f"Solution: {exercise.title}", exercise.solution_code)
            _write_code_file(out("test.py"), f"Unit Tests: {exercise.title}", exercise.unit_test)
            if starter_code:
                gates.run_gate("G3 scaffold", lambda: gates.scaffold_gate(
                    exercise.starter_code, exercise.solution_code, exercise.unit_test, clean_id, run.artifact_source_dirs), trace)

            # 5. Agentic 16:9 Presentation Generation
            print(f"5. Synthesizing domain-grounded presentation deck via Presentation Designer ({module.id})...")
            presentation_payload = build_presentation_payload(
                module=module,
                problem_formulation=problem_formulation,
                solution_code=solution_code,
                telemetry=telemetry
            )
            write_file(out("slides_payload.json"), lambda f: json.dump(presentation_payload, f, indent=2))

            saved_deck = presentation_designer.generate_presentation_deck(
                module=module,
                problem_formulation=problem_formulation,
                solution_code=solution_code,
                telemetry=telemetry,
                output_path=out("presentation.pptx"),
                artifacts=collect_deck_artifacts(run.telemetry_dir, telemetry),
                trace=trace
            )
            if not (saved_deck and os.path.exists(saved_deck)):
                raise RuntimeError(f"Presentation deck was not generated for module '{module.id}'.")
            print(f"  -> Saved AI Presentation Deck: {saved_deck}")
            print(f"  -> Saved all module assets to '{week_dir}/'")
            result.ok = True

        except Exception as mod_err:
            print(f"[ERROR] Failed processing module {module.id} (Week {module.week}): {mod_err}")
            traceback.print_exc()
            result.error = str(mod_err)
        finally:
            if gates.RECORDS:  # also for a failed week: what the gates saw before it failed
                write_file(out("gates.json"), lambda f: json.dump(gates.RECORDS, f, indent=2))
            result.trace = trace.save()
            print(f"  -> Saved PROV generation trace: {trace.path()}")
    result.minutes = (time.monotonic() - started) / 60
    return result
