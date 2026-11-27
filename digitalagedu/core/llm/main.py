"""Phase 2 orchestration: plans the course's weeks, writes each week's problem statement in order (Stage A),
builds the weeks in parallel worker processes (Stage B, see week_builder.py), then records provenance and the
run's verdict (Stage C, see lineage.py)."""
import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Optional, List, Dict, Any

from digitalagedu.core.config import load_config
from digitalagedu.core.writer import write_file
from digitalagedu.core.llm.schemas import Module, SyllabusPlanSchema
from digitalagedu.core.llm import ai_setup
from digitalagedu.core.llm.ai_setup import (
    get_instructor_client, get_openai_client, configure_model_slots, calls_nrp_directly,
)
from digitalagedu.core.llm.telemetry import load_phase1_telemetry, formulate_problem_statement
from digitalagedu.core.llm.syllabus_architect import formulate_syllabus, modules_from_plan
from digitalagedu.core.eval.load import latest_formulation, list_finished_weeks
from digitalagedu.core.llm.sandbox import describe_sandbox_fixtures
from digitalagedu.core.llm import lineage
from digitalagedu.core.llm.week_builder import WeekRun, WeekResult, build_week, finished_week, init_worker

# The packages students install for every week; Phase 1 packaging writes the same list (run_pipeline.py)
STUDENT_REQUIREMENTS = (
    "numpy>=1.24\n"
    "pandas>=2.0\n"
    "matplotlib>=3.7\n"
    "seaborn>=0.13\n"
    "pillow>=10.0\n"
    "opencv-python>=4.8\n"
    "gradio>=4.0\n"
    "torch>=2.0\n"
    "torchvision>=0.15\n"
    "scikit-learn>=1.0\n"
    "scikit-image>=0.21\n"
    "scipy>=1.10\n"
    "timm>=0.9\n"
    "segment-anything>=1.0\n"
)


def _write_syllabus(syllabus_plan: SyllabusPlanSchema, curriculum: Any, num_weeks: int, output_dir: str):
    """Saves the Syllabus Architect plan as syllabus_plan.json and course_syllabus.md."""
    syllabus_json_path = os.path.join(output_dir, "syllabus_plan.json")
    write_file(syllabus_json_path, lambda f: f.write(syllabus_plan.model_dump_json(indent=2)))
    print(f"  -> Saved Syllabus Plan JSON: {syllabus_json_path}")

    syllabus_md_path = os.path.join(output_dir, "course_syllabus.md")
    def fill(f):
        f.write(f"# {syllabus_plan.course_title}\n\n")
        f.write(f"**Target Level:** {curriculum.level} | **Duration:** {num_weeks} Weeks\n\n")
        f.write(f"## Course Description\n{syllabus_plan.course_description}\n\n")
        f.write(f"## Weekly Syllabus\n")
        for m in syllabus_plan.modules:
            f.write(f"### Week {m.week}: {m.title}\n")
            f.write(f"- **Difficulty:** {m.difficulty}\n")
            f.write(f"- **Focus:** {m.context}\n")
            if m.learning_outcomes:
                f.write(f"- **Learning Outcomes:**\n")
                for lo in m.learning_outcomes:
                    f.write(f"  - {lo}\n")
            f.write("\n")
    write_file(syllabus_md_path, fill)
    print(f"  -> Saved Course Syllabus Markdown: {syllabus_md_path}")


def _build_modules(root_config: Any, telemetry: Dict[str, Any], client, model_name: str, output_dir: str) -> List[Module]:
    """Modules from explicit YAML modules, else YAML topics, else a saved syllabus (Phase 2 rerun), else the
    Syllabus Architect agent; sorted by week."""
    curriculum = root_config.curriculum
    project = getattr(root_config, "project", None)
    topics = getattr(curriculum, "topics", None) or []
    topic_focus = "; ".join(
        f"{t.name}: {t.description}".strip(": ")
        for t in topics
        if getattr(t, "name", None) or getattr(t, "description", None)
    )
    resources = [
        {"name": getattr(r, "name", "") or "", "url": getattr(r, "url", "") or ""}
        for r in (getattr(curriculum, "resources", None) or [])
        if getattr(r, "name", None) or getattr(r, "url", None)
    ]
    course_meta: Dict[str, Any] = {
        "domain": getattr(project, "domain", "") or "",
        "course_context": getattr(project, "context_statement", "") or "",
        "subject": getattr(curriculum, "subject", "") or "",
        "topic_focus": topic_focus,
        "resources": resources,
    }
    modules_list = []

    if getattr(curriculum, "modules", None) and len(curriculum.modules) > 0:
        print("[Curriculum Config] Using explicit modules defined in YAML configuration.")
        for m in curriculum.modules:
            modules_list.append(
                Module(
                    id=m.id,
                    title=getattr(m, "title", None) or m.id.replace("_", " ").replace("-", " ").title(),
                    week=m.week or 1,
                    context=getattr(m, "context", None) or f"{curriculum.subject} ({m.id})",
                    difficulty=getattr(m, "difficulty", None) or "intermediate",
                    learning_outcomes=getattr(m, "learning_outcomes", None) or [],
                    level=curriculum.level,
                    estimated_days=getattr(m, "estimated_days", None),
                    **course_meta,
                )
            )
    elif topics:
        print("[Curriculum Config] Using explicit topics defined in YAML configuration.")
        for i, t in enumerate(topics):
            modules_list.append(
                Module(
                    id=f"topic_{i+1}",
                    title=t.name,
                    week=i + 1,
                    context=f"{t.description} ({t.project})",
                    difficulty="intermediate",
                    level=curriculum.level,
                    **course_meta,
                )
            )
    elif os.path.isfile(os.path.join(output_dir, "syllabus_plan.json")):
        # A Phase 2 rerun of failed weeks copies the original syllabus here, so its weeks keep their ids and folders
        print("[Syllabus Architect] Reusing the saved syllabus_plan.json (Phase 2 rerun).")
        with open(os.path.join(output_dir, "syllabus_plan.json"), encoding="utf-8") as f:
            modules_list = [
                mod.model_copy(update=course_meta)
                for mod in modules_from_plan(SyllabusPlanSchema.model_validate_json(f.read()), curriculum.level)
            ]
    else:
        print("\n[Syllabus Architect] No explicit modules provided in YAML. Autonomously formulating complete curriculum...")
        syllabus_plan, planned_modules = formulate_syllabus(root_config, telemetry, client, model_name)
        modules_list = [mod.model_copy(update=course_meta) for mod in planned_modules]
        _write_syllabus(syllabus_plan, curriculum, len(modules_list), output_dir)

    modules_list.sort(key=lambda m: (m.week if m.week is not None else 999, m.id))
    return modules_list


def _history_entry(module: Module, focus: Optional[str], components: List[str]) -> Dict[str, Any]:
    """What later weeks' problem statements see of an earlier week (cumulative memory)."""
    return {"week": module.week, "title": module.title, "focus": focus, "components": components[:6]}


def generate_llm_curriculum(
    config_path: str,
    output_dir: Optional[str] = None,
    telemetry_dir: Optional[str] = None,
    base_url: Optional[str] = None,
):
    """Main orchestration function executing 3-Agent LLM Curriculum Generation."""
    root_config = load_config(config_path)
    base_out = root_config.output.directory if root_config.output else "./output"
    output_dir = output_dir or os.path.join(base_out, "exercises")
    telemetry_dir = telemetry_dir or base_out
    base_url = base_url or root_config.execution.llm_base_url
    models = root_config.execution.llm_models

    print(f"\n[Phase 2 LLM Pipeline] Endpoint: {base_url or 'default'} | Models: "
          + ", ".join(f"{role}={name}" for role, name in models.model_dump().items()))
    client = get_instructor_client(base_url=base_url)
    code_client = get_openai_client(base_url=base_url)
    # Week worker processes build their own clients (WeekRun.with_clients): with the NRP key on direct-NRP runs, else
    # None, so each mints its own Tapis access tokens for the LLM proxy from TAPIS_REFRESH_TOKEN (llm_api_key)
    api_key = os.getenv("NRP_LLM_API") if calls_nrp_directly(base_url) else None
    # The clients hold the key now; slide code runs in-process (exec), so it must not find it in os.environ
    os.environ.pop("NRP_LLM_API", None)
    os.makedirs(output_dir, exist_ok=True)

    telemetry = load_phase1_telemetry(telemetry_dir)
    if telemetry:
        print(f"[Telemetry Loaded] Found telemetry from Phase 1 output dir: {telemetry_dir}")

    modules_list = _build_modules(root_config, telemetry, client, models.planner, output_dir)
    if not modules_list:
        print("[WARNING] No curriculum modules could be formulated. Exiting Phase 2.")
        return

    run = WeekRun(
        models=models, root_config=root_config, config_path=config_path, telemetry=telemetry,
        telemetry_dir=telemetry_dir, output_dir=output_dir,
        known_manifest=telemetry.get("artifact_manifest", []) or telemetry.get("provenance", {}).get("artifact_manifest", []),
        artifact_source_dirs=[telemetry_dir] if telemetry_dir and os.path.exists(telemetry_dir) else [],
        fixture_note="\n\n" + describe_sandbox_fixtures(telemetry_dir),
        base_url=base_url, api_key=api_key, client=client, code_client=code_client,
    )

    # Stage A, in order: each week's problem statement sees what the earlier weeks cover (cumulative memory),
    # so it is the one step that cannot run in parallel
    prepared: Dict[str, tuple] = {}
    curriculum_history: List[Dict[str, Any]] = []
    # Weeks a Phase 2 rerun copied over finished (verified, with a deck); none on a fresh run
    finished = {os.path.basename(d): d for d in list_finished_weeks(output_dir)}
    for module in modules_list:
        done_dir = finished.get(module.id.replace("-", "_"))
        if done_dir:
            print(f"0. Week {module.week} ({module.id}) is already finished; kept as is")
            formulation = latest_formulation(done_dir)
            curriculum_history.append(_history_entry(module, formulation.get("suggested_focus"), [
                c.get("name") for sub in (formulation.get("milestone_subsystems") or []) for c in sub.get("components") or []]))
            continue
        print(f"0. Agent 0: Formulating problem statement & subsystem contracts (Week {module.week}: {module.id})...")
        snapshot = list(curriculum_history)
        try:
            formulation = formulate_problem_statement(
                module=module, telemetry=telemetry, client=client, model_name=models.planner,
                curriculum_history=snapshot, revision_feedback=None, fixture_note=run.fixture_note,
            )
        except Exception as err:
            print(f"  -> Notice: Week {module.week}'s problem statement failed here ({err}); its worker retries it")
            formulation = None
        prepared[module.id] = (formulation, snapshot)
        if formulation is not None:
            curriculum_history.append(_history_entry(module, formulation.suggested_focus, [
                c.name for sub in (getattr(formulation, "milestone_subsystems", None) or []) for c in sub.components]))

    # Stage B: the rest of each week (tests, solution, sandbox, starter code, deck) in parallel worker processes.
    # Processes, not threads: the slide REPL patches pyplot and slide_kit globals, and pyplot is not thread-safe.
    # Spawned, not forked: Stage A's RAG lookups start torch's thread pool, and a fork after that can deadlock.
    caps = dict(root_config.execution.llm_concurrency or {})
    workers = root_config.execution.parallel_weeks or caps.get(models.coder) or 1
    todo = [m for m in modules_list if m.id in prepared]
    workers = max(1, min(workers, len(todo)))
    mp_ctx = multiprocessing.get_context("spawn")
    configure_model_slots(caps, mp_ctx)  # handed to every worker, so all of them share the same per-model caps
    print(f"\n[Phase 2] Building {len(todo)} week(s), {workers} at a time "
          f"(caps {caps or 'none'}); each week logs to Week_XX/<module>/<module>_phase2.log")

    results: List[WeekResult] = []
    generation_traces: List[tuple] = []

    def collect(result: WeekResult) -> None:
        results.append(result)
        status = "finished" if result.ok else f"FAILED: {result.error}"
        print(f"[Week {result.week}] {status} ({result.minutes:.0f} min) | log: {result.log}")
        if not result.ok and result.log and os.path.exists(result.log):
            with open(result.log, encoding="utf-8", errors="replace") as f:
                print("".join(f.readlines()[-40:]).rstrip())  # the error without opening the week's log
        if result.trace:
            # Saved and linked even on a crash: the trace is the proof of where the module failed
            generation_traces.append((result.module_id, result.trace))
            lineage.register_generation_traces(telemetry_dir, generation_traces)

    for module in modules_list:
        if module.id not in prepared:  # finished in the run being rerun: counted as done, with its saved lineage
            collect(finished_week(module, finished[module.id.replace("-", "_")]))

    if workers == 1:
        for module in todo:
            print(f"[Week {module.week}] started: {module.title}")
            collect(build_week(run, module, *prepared[module.id]))
    else:
        worker_run = run.for_worker()  # each worker builds its own clients
        with ProcessPoolExecutor(max_workers=workers, mp_context=mp_ctx, initializer=init_worker,
                                 initargs=(dict(ai_setup.MODEL_SLOTS),)) as pool:
            futures = {}
            for module in todo:
                print(f"[Week {module.week}] started: {module.title}")
                futures[pool.submit(build_week, worker_run, module, *prepared[module.id])] = module
            for future in as_completed(futures):
                module = futures[future]
                try:
                    collect(future.result())
                except Exception as err:  # the worker process itself died, e.g. out of memory
                    collect(WeekResult(module.id, module.week, error=f"worker crashed: {err!r}"))

    # Stage C: provenance and the run's verdict, written only here in the parent
    write_file(os.path.join(output_dir, "requirements.txt"), lambda f: f.write(STUDENT_REQUIREMENTS))

    # Reconcile provenance.json with LLM Agent 0 evaluated artifact bindings; only completed modules are recorded
    lineage.reconcile_module_bindings(
        telemetry_dir, {r.module_id.replace("-", "_"): r.source_arts for r in results if r.ok})

    failed_modules = [f"{r.module_id} (Week {r.week}): {r.error}" for r in sorted(results, key=lambda r: r.week)
                      if not r.ok]  # a failed week doesn't stop the others; the run still fails at the end
    _pedagogy_eval(root_config, output_dir, telemetry_dir, client)
    if failed_modules:
        raise RuntimeError(f"Phase 2 finished with {len(failed_modules)} of {len(modules_list)} module(s) failed:\n"
                           + "\n".join(failed_modules))
    print(f"\n[SUCCESS] Phase 2 LLM curriculum generation complete! Output: {output_dir}")


def _pedagogy_eval(root_config: Any, output_dir: str, telemetry_dir: Optional[str], client) -> None:
    """Pilot scoring of the finished weeks (execution.pedagogy_eval). Log-only: it runs after every material is written,
    writes only to <output_dir>/evaluation/, and any error is printed, never raised, so the run's outcome is unchanged."""
    execution = root_config.execution
    if not getattr(execution, "pedagogy_eval", False):
        return
    try:
        from digitalagedu.core.eval.run import evaluate_run
        evaluate_run(output_dir, telemetry_dir, root_config, client, execution.llm_models.judge,
                     budget_minutes=execution.pedagogy_eval_minutes)
    except Exception as err:
        print(f"[Pedagogy Eval] Skipped after an error (generation unaffected): {err!r}")
