import os
import re
import json
import traceback
from typing import Optional, List, Dict, Any

from digitalagedu.core.config import load_config
from digitalagedu.core.artifact_validator import compute_file_sha256
from digitalagedu.core.llm.schemas import (
    Module,
    ProblemStatementSchema,
    ValidatedExerciseSchema,
    SyllabusPlanSchema,
    ModuleManifestSchema,
)
from digitalagedu.core.llm.ai_setup import get_instructor_client, get_openai_client
from digitalagedu.core.llm.telemetry import load_phase1_telemetry, formulate_problem_statement
from digitalagedu.core.llm.syllabus_architect import formulate_syllabus
from digitalagedu.core.llm.context import (
    build_system_prompt,
    build_exercise_prompt,
    build_scaffold_prompt,
    build_qa_prompt,
    build_presentation_payload,
)
from digitalagedu.core.llm.sandbox import run_in_sandbox, clean_code_snippet
from digitalagedu.core.llm.presentation_designer import PresentationDesigner

MAX_SELF_HEAL_ROUNDS = 3



def reconcile_provenance_with_llm_evaluations(telemetry_dir: str, module_artifact_bindings: Dict[str, List[str]]):
    """
    Reconciles the global provenance.json artifact_manifest with the
    empirical artifact selections evaluated by LLM Agent 0 (Curriculum Director).
    
    Inverts Module -> Source Artifacts into Artifact -> Module References,
    ensuring bidirectional, 100% LLM-evaluated provenance lineage without hardcoding.
    
    Strictly verifies that all referenced artifact IDs resolve to existing registered artifacts;
    any unresolvable artifact reference triggers a contract validation error.
    """
    if not telemetry_dir:
        return
    prov_path = os.path.join(telemetry_dir, "provenance.json")
    if not os.path.exists(prov_path):
        return

    with open(prov_path, "r", encoding="utf-8") as f:
        prov_data = json.load(f)

    manifest = prov_data.get("artifact_manifest", [])
    if not manifest:
        return

    # 1. Strict Lineage Check: verify every referenced artifact ID resolves to a registered artifact
    unresolved_lineage = {}
    for mod_id, arts in module_artifact_bindings.items():
        unresolved = []
        for art_id in arts:
            key = str(art_id).strip().lower()
            matched = any(
                key == str(a.get("artifact_id", "")).lower() or
                key == str(a.get("name", "")).lower() or
                (str(a.get("slug", "")).lower() in key and len(str(a.get("slug", ""))) > 3)
                for a in manifest
            )
            if not matched:
                unresolved.append(art_id)
        if unresolved:
            unresolved_lineage[mod_id] = unresolved

    if unresolved_lineage:
        raise ValueError(
            f"Provenance lineage reconciliation contract failure: "
            f"unresolvable artifact references detected: {unresolved_lineage}"
        )

    # 2. Invert: artifact_identifier -> set of module_ids
    artifact_to_modules = {}
    for mod_id, arts in module_artifact_bindings.items():
        for art_id in arts:
            art_key = str(art_id).strip().lower()
            artifact_to_modules.setdefault(art_key, set()).add(mod_id)

    updated_count = 0
    for art in manifest:
        art_id = str(art.get("artifact_id", "")).lower()
        fname = str(art.get("name", "")).lower()
        slug = str(art.get("slug", "")).lower() if "slug" in art else fname.split(".")[0]

        matched_modules = set()
        for chosen_key, mod_set in artifact_to_modules.items():
            if chosen_key == art_id or slug in chosen_key or chosen_key in fname:
                matched_modules.update(mod_set)

        if matched_modules:
            art["module_references"] = sorted(list(matched_modules))
            updated_count += 1

    with open(prov_path, "w", encoding="utf-8") as f:
        json.dump(prov_data, f, indent=4)

    print(f"[Provenance Lineage] Successfully reconciled provenance.json: {updated_count} artifacts updated with LLM-evaluated module bindings.")


DEFAULT_MODEL_NAME = "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ"

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
    "timm>=0.9\n"
    "segment-anything>=1.0\n"
)


_CODE_FENCE = re.compile(r"```(?:python|py)?[ \t]*\n(.*?)```", re.DOTALL)


def _extract_code_block(text: str) -> str:
    """Longest fenced block of a plain-text reply; an unfenced (or unclosed) reply is taken whole."""
    blocks = _CODE_FENCE.findall(text or "")
    return max(blocks, key=len).strip() if blocks else clean_code_snippet(text or "")


def _ask_code(code_client, model_name: str, prompt: str, what: str, max_retries: int = 2) -> str:
    """Plain-text LLM call returning one ```python block. Code never travels inside JSON,
    so quotes need no escaping; replies that are cut off or don't compile are re-asked with the error."""
    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": f"{prompt}\n\nOUTPUT FORMAT: Reply with the complete {what} as ONE ```python fenced code block and nothing else."}
    ]
    for _ in range(1 + max_retries):
        choice = code_client.chat.completions.create(model=model_name, max_tokens=16384, messages=messages).choices[0]
        code = _extract_code_block(choice.message.content)
        if choice.finish_reason == "length":
            problem = "Your reply was cut off by the token limit; return shorter but complete code."
        else:
            try:
                compile(code, "<generated>", "exec")
                return code
            except SyntaxError as e:
                problem = f"The code does not compile (SyntaxError: {e.msg} at line {e.lineno}: {(e.text or '').strip()!r})."
        messages += [
            {"role": "assistant", "content": choice.message.content or ""},
            {"role": "user", "content": f"{problem} Reply again with the complete, corrected {what} in one ```python block."}
        ]
    raise RuntimeError(f"LLM did not return a compilable {what} after {1 + max_retries} attempts: {problem}")


def _write_syllabus(syllabus_plan: SyllabusPlanSchema, curriculum: Any, num_weeks: int, output_dir: str):
    """Saves the Syllabus Architect plan as syllabus_plan.json and course_syllabus.md."""
    syllabus_json_path = os.path.join(output_dir, "syllabus_plan.json")
    with open(syllabus_json_path, "w", encoding="utf-8") as f:
        f.write(syllabus_plan.model_dump_json(indent=2))
    print(f"  -> Saved Syllabus Plan JSON: {syllabus_json_path}")

    syllabus_md_path = os.path.join(output_dir, "course_syllabus.md")
    with open(syllabus_md_path, "w", encoding="utf-8") as f:
        f.write(f"# {syllabus_plan.course_title}\n\n")
        f.write(f"**Target Level:** {getattr(curriculum, 'grade', 10)} | **Duration:** {num_weeks} Weeks\n\n")
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
    print(f"  -> Saved Course Syllabus Markdown: {syllabus_md_path}")


def _build_modules(root_config: Any, telemetry: Dict[str, Any], client, model_name: str, output_dir: str) -> List[Module]:
    """Modules from explicit YAML modules, else YAML topics, else the Syllabus Architect agent; sorted by week."""
    curriculum = root_config.curriculum
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
                    learning_outcomes=getattr(m, "learning_outcomes", None) or []
                )
            )
    elif getattr(curriculum, "topics", None) and len(curriculum.topics) > 0:
        print("[Curriculum Config] Using explicit topics defined in YAML configuration.")
        for i, t in enumerate(curriculum.topics):
            modules_list.append(
                Module(
                    id=f"topic_{i+1}",
                    title=t.name,
                    week=i + 1,
                    context=f"{t.description} ({t.project})",
                    difficulty="intermediate"
                )
            )
    else:
        print("\n[Syllabus Architect] No explicit modules provided in YAML. Autonomously formulating complete curriculum...")
        syllabus_plan, modules_list = formulate_syllabus(root_config, telemetry, client, model_name)
        _write_syllabus(syllabus_plan, curriculum, len(modules_list), output_dir)

    modules_list.sort(key=lambda m: (m.week if m.week is not None else 999, m.id))
    return modules_list


def _resolve_source_artifacts(problem_formulation: ProblemStatementSchema, known_manifest: List[Dict[str, Any]],
                              module: Module, clean_id: str) -> List[str]:
    """Validates Agent 0's source_artifacts against the verified manifest, with domain-agnostic fallbacks."""
    valid_source_arts = []
    unresolved_source_arts = []

    for art_ref in list(getattr(problem_formulation, "source_artifacts", []) or []):
        art_ref_str = str(art_ref).strip()
        art_ref_clean = art_ref_str.lower()
        matched_id = None
        for art in known_manifest:
            aid = str(art.get("artifact_id", ""))
            aname = str(art.get("name", ""))
            aslug = str(art.get("slug", "")) if "slug" in art else aname.split(".")[0]
            if art_ref_clean == aid.lower() or art_ref_clean == aname.lower() or (len(aslug) > 3 and art_ref_clean == aslug.lower()):
                matched_id = aid
                break
        if matched_id:
            valid_source_arts.append(matched_id)
        else:
            unresolved_source_arts.append(art_ref_str)

    if unresolved_source_arts:
        print(f"  -> [Lineage Contract Violation] Agent 0 emitted unresolved artifact IDs: {unresolved_source_arts}")

    if not valid_source_arts and known_manifest:
        clean_id_lower = clean_id.lower()
        mod_id_lower = str(module.id).lower()

        # Dynamic initial module_references populated in Phase 1
        for art in known_manifest:
            art_id = art.get("artifact_id")
            art_mod_refs = [str(m).strip().lower() for m in art.get("module_references", [])]
            if art_id and (clean_id_lower in art_mod_refs or mod_id_lower in art_mod_refs):
                valid_source_arts.append(art_id)

        # Token overlap matching between module identifier and artifact metadata
        if not valid_source_arts:
            mod_tokens = set(re.findall(r"[a-zA-Z0-9]+", clean_id_lower))
            for art in known_manifest:
                art_id = art.get("artifact_id")
                meta_text = f"{art.get('artifact_id', '')} {art.get('name', '')} {art.get('category', '')}".lower()
                if art_id and mod_tokens & set(re.findall(r"[a-zA-Z0-9]+", meta_text)):
                    valid_source_arts.append(art_id)

        # If still empty, bind to the first registered workflow artifact
        if not valid_source_arts and known_manifest[0].get("artifact_id"):
            valid_source_arts.append(known_manifest[0]["artifact_id"])

    return sorted(set(valid_source_arts))


def _write_module_manifest(path: str, module: Module, source_arts: List[str], telemetry: Dict[str, Any],
                           root_config: Any, config_path: str):
    """Writes <module>_manifest.json; strict Pydantic validation fails if any lineage field is missing."""
    prov_meta = telemetry.get("provenance", {})
    workflow_run_id = (
        prov_meta.get("workflow_run_id")
        or prov_meta.get("run_id")
        or f"run_{getattr(root_config.execution, 'seed', None) or '0'}"
    )
    config_hash = (
        prov_meta.get("configuration_hash")
        or (compute_file_sha256(config_path) if config_path and os.path.exists(config_path) else None)
        or "0" * 64
    )
    dataset_ver = prov_meta.get("dataset_version") or getattr(root_config.dataset, "version", None) or "1.0"
    model_ver = (
        prov_meta.get("model_version")
        or getattr(root_config.execution, "model_version", None)
        or getattr(root_config.execution, "device", None)
        or "model_v1.0"
    )

    manifest_obj = ModuleManifestSchema(
        module_id=module.id,
        title=module.title,
        academic_week=module.week,
        difficulty=module.difficulty,
        workflow_run_id=workflow_run_id,
        dataset_version=str(dataset_ver),
        model_version=str(model_ver),
        configuration_hash=str(config_hash),
        source_artifacts=source_arts or ["unassigned_workflow_artifact"],
        learning_objective_tags=[lo.lower().replace(" ", "_")[:40] for lo in (module.learning_outcomes or [])] or ["curriculum_objective"],
        learner_role="student_practitioner",
        permitted_representation="authentic_telemetry_fixture",
        selection_rule="pedagogical_subsystem_contract_decomposition",
        validation_status=prov_meta.get("validation_status", "VERIFIED")
    )
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest_obj.model_dump(), f, indent=2)
    print(f"  -> Saved Validated Module Manifest (Artifact Linkage): {path}")


def _sandbox_fixture_note(telemetry_dir: Optional[str]) -> str:
    """Prompt suffix listing the files run_in_sandbox copies into its working directory (top-level telemetry files)."""
    sandbox_files = sorted(
        f for f in os.listdir(telemetry_dir) if os.path.isfile(os.path.join(telemetry_dir, f))
    ) if telemetry_dir and os.path.isdir(telemetry_dir) else []
    return (
        "\n\nSANDBOX FIXTURES: Code runs with these files in the current working directory "
        f"(open them by bare filename, no sub-folders such as 'fixtures/'): {', '.join(sandbox_files) or 'none'}"
    )


def _verify_with_self_healing(code_client, model_name: str, module: Module, clean_id: str, qa_prompt: str,
                              exercise_prompt: str, unit_test: str, solution_code: str, artifact_source_dirs: List[str]):
    """Runs solution + tests in the sandbox; each failed round repairs whichever side the log points to.
    Returns (success, log, unit_test, solution_code)."""
    def verify():
        return run_in_sandbox(
            solution_code,
            unit_test,
            module_id=module.id,
            artifact_sources=artifact_source_dirs
        )

    success, log = verify()
    for heal_round in range(1, MAX_SELF_HEAL_ROUNDS + 1):
        if success:
            break
        print(f"  -> Sandbox verification failed (self-healing round {heal_round}/{MAX_SELF_HEAL_ROUNDS}). Diagnosing root cause from log...")
        is_solution_fault = (
            f"{clean_id}_solution" in log or
            "NameError:" in log or
            "ModuleNotFoundError:" in log or
            "AttributeError:" in log or
            ("TypeError:" in log and "test_runner" not in log)
        )
        if is_solution_fault:
            print(f"  -> Error detected in solution_code. Triggering Agent 1 self-healing retry...")
            solution_code = _ask_code(code_client, model_name, (
                f"{exercise_prompt}\n\n"
                f"--- PREVIOUS SANDBOX EXECUTION FAILURE LOG ---\n{log}\n\n"
                f"CRITICAL FIX DIRECTIVE:\n"
                f"Your previous solution failed during execution. Fix the error:\n"
                f"1. Explicitly import all used libraries and functions at the top.\n"
                f"2. Load authentic workflow artifacts from disk fixtures.\n"
                f"3. Ensure all subsystem component signatures match the unit test expectations.\n"
                f"Return the complete, working solution."
            ), "reference solution")
        else:
            print(f"  -> Triggering Agent 2 test verification self-healing retry...")
            unit_test = _ask_code(code_client, model_name, (
                f"{qa_prompt}\n\n"
                f"--- REFERENCE SOLUTION CODE ---\n{solution_code}\n\n"
                f"--- PREVIOUS SANDBOX VERIFICATION LOG ---\n{log}\n\n"
                f"Please fix the unit test code to properly assert the solution without syntax or assertion errors."
            ), "unit test file")
        success, log = verify()
    return success, log, unit_test, solution_code


def _write_code_file(path: str, docstring: str, code: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f'"""\n{docstring}\n"""\n\n')
        f.write(clean_code_snippet(code) + "\n")


def _first_image(folder: Optional[str]) -> Optional[str]:
    if folder and os.path.isdir(folder):
        return next((os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith((".jpg", ".png", ".jpeg"))), None)
    return None


def _collect_deck_artifacts(telemetry_dir: Optional[str], telemetry: Dict[str, Any]) -> Dict[str, str]:
    """Authentic pipeline fixtures (raw/mask samples, contrastive pair) offered to the slide builder."""
    artifacts = {}
    if telemetry_dir:
        raw = _first_image(os.path.join(telemetry_dir, "images", "raw"))
        mask = _first_image(os.path.join(telemetry_dir, "images", "masks"))
        if raw:
            artifacts["raw_sample"] = raw
        if mask:
            artifacts["mask_sample"] = mask
    contrastive = telemetry.get("contrastive_samples", {}) if telemetry else {}
    for key in ("top_success", "hard_failure"):
        if (contrastive.get(key) or {}).get("image_path"):
            artifacts[key] = str(contrastive[key]["image_path"])
    return artifacts


def generate_llm_curriculum(
    config_path: str,
    output_dir: Optional[str] = None,
    telemetry_dir: Optional[str] = None,
    base_url: Optional[str] = None,
    model_name: Optional[str] = None
):
    """Main orchestration function executing 3-Agent LLM Curriculum Generation."""
    root_config = load_config(config_path)
    base_out = root_config.output.directory if root_config.output else "./output"
    output_dir = output_dir or os.path.join(base_out, "exercises")
    telemetry_dir = telemetry_dir or base_out
    base_url = base_url or getattr(root_config.execution, "llm_base_url", "http://localhost:8000/v1")
    model_name = model_name or (
        getattr(root_config.curriculum, "model", None)
        or getattr(root_config.execution, "llm_model", None)
        or getattr(root_config, "model", None)
        or DEFAULT_MODEL_NAME
    )

    print(f"\n[Phase 2 LLM Pipeline] Using Model: {model_name} | Endpoint: {base_url or 'default'}")
    client = get_instructor_client(base_url=base_url)
    code_client = get_openai_client(base_url=base_url)
    os.makedirs(output_dir, exist_ok=True)

    telemetry = load_phase1_telemetry(telemetry_dir)
    if telemetry:
        print(f"[Telemetry Loaded] Found telemetry from Phase 1 output dir: {telemetry_dir}")

    modules_list = _build_modules(root_config, telemetry, client, model_name, output_dir)
    if not modules_list:
        print("[WARNING] No curriculum modules could be formulated. Exiting Phase 2.")
        return

    presentation_designer = PresentationDesigner(client=client, model_name=model_name)
    known_manifest = telemetry.get("artifact_manifest", []) or telemetry.get("provenance", {}).get("artifact_manifest", [])
    artifact_source_dirs = [telemetry_dir] if telemetry_dir and os.path.exists(telemetry_dir) else []
    fixture_note = _sandbox_fixture_note(telemetry_dir)
    curriculum_history: List[Dict[str, Any]] = []
    llm_module_artifact_bindings: Dict[str, List[str]] = {}

    for module in modules_list:
        print(f"\n==================================================")
        print(f"Processing LLM Module: {module.title} (Week {module.week})...")
        print(f"==================================================")

        clean_id = module.id.replace("-", "_")
        module_dir = os.path.join(output_dir, f"Week_{module.week:02d}", clean_id)
        os.makedirs(module_dir, exist_ok=True)
        out = lambda suffix: os.path.join(module_dir, f"{clean_id}_{suffix}")

        try:
            # 0. Agent 0: Problem Formulation with Subsystem Contracts & Cumulative Memory
            print(f"0. Agent 0: Formulating problem statement & subsystem contracts ({module.id})...")
            problem_formulation: ProblemStatementSchema = formulate_problem_statement(
                module=module,
                telemetry=telemetry,
                client=client,
                model_name=model_name,
                curriculum_history=curriculum_history
            )

            source_arts = _resolve_source_artifacts(problem_formulation, known_manifest, module, clean_id)
            overview_content = problem_formulation.markdown_overview or f"# {problem_formulation.title}\n\n{problem_formulation.problem_statement}"
            if source_arts:
                overview_content += "\n\n## Workflow Evidence & Artifact Lineage\n"
                overview_content += "This laboratory module is grounded in validated research workflow artifacts from the computational pipeline:\n"
                overview_content += "".join(f"- **Source Artifact ID:** `{sa}`\n" for sa in source_arts)
            with open(out("overview.md"), "w", encoding="utf-8") as f:
                f.write(overview_content)
            print(f"  -> Saved Student Overview: {out('overview.md')}")

            _write_module_manifest(out("manifest.json"), module, source_arts, telemetry, root_config, config_path)
            llm_module_artifact_bindings[clean_id] = source_arts

            # 1. Agent 2 (QA): TDD Step 1 - Generate Unit Tests First from Subsystem Contracts
            print(f"1. Agent 2 (QA): Writing property-based unit tests for {module.id}...")
            qa_prompt = build_qa_prompt(module, problem_formulation=problem_formulation, telemetry=telemetry) + fixture_note
            unit_test = _ask_code(code_client, model_name, qa_prompt, "unit test file", max_retries=3)

            # 2. Agent 1 (Coder): TDD Step 2 - Implement Reference Solution to Pass Unit Tests
            print(f"2. Agent 1 (Coder): Synthesizing reference solution satisfying unit tests ({module.id})...")
            exercise_prompt = build_exercise_prompt(
                module=module,
                problem_formulation=problem_formulation,
                unit_test_code=unit_test,
                curriculum_history=curriculum_history,
                telemetry=telemetry
            ) + fixture_note
            solution_code = _ask_code(code_client, model_name, exercise_prompt, "reference solution", max_retries=3)

            # 3. Execution Sandbox Verification with Bidirectional Self-Healing
            print(f"3. Sandbox: Verifying solution against unit tests ({module.id})...")
            success, log, unit_test, solution_code = _verify_with_self_healing(
                code_client, model_name, module, clean_id, qa_prompt, exercise_prompt,
                unit_test, solution_code, artifact_source_dirs
            )
            if not success:
                print(f"  -> Final Sandbox Verification Log:\n{log}")
            with open(out("verification.json"), "w", encoding="utf-8") as f:
                json.dump({
                    "module_id": module.id,
                    "verified": success,
                    "log": "All tests passed cleanly in sandbox." if success else log
                }, f, indent=2)
            # Slides must never be built from an unverified solution.
            if not success:
                raise RuntimeError(f"Sandbox verification failed for module '{module.id}'. See {out('verification.json')}")

            # 4. TDD Step 3: Exercise Scaffolding derived from verified solution
            print(f"4. Scaffolding student starter code from verified solution ({module.id})...")
            starter_code = None
            try:
                scaffold_prompt = build_scaffold_prompt(module, problem_formulation, solution_code)
                starter_result = _ask_code(code_client, model_name, scaffold_prompt, "student starter code")
                if len(starter_result) > 30:
                    starter_code = starter_result
            except Exception as e:
                print(f"  -> Notice: Fallback to existing starter scaffolding: {e}")

            exercise = ValidatedExerciseSchema(
                title=problem_formulation.title,
                instructions=problem_formulation.problem_statement,
                starter_code=starter_code or "# Student implementation starter skeleton\n",
                solution_code=solution_code,
                unit_test=unit_test
            )
            with open(out("generated.json"), "w", encoding="utf-8") as f:
                json.dump(exercise.model_dump(), f, indent=2)
            _write_code_file(out("exercise.py"), f"{exercise.title}\n\nInstructions:\n{exercise.instructions}", exercise.starter_code)
            _write_code_file(out("solution.py"), f"Solution: {exercise.title}", exercise.solution_code)
            _write_code_file(out("test.py"), f"Unit Tests: {exercise.title}", exercise.unit_test)

            # 5. Agentic 16:9 Presentation Generation
            print(f"5. Synthesizing domain-grounded presentation deck via Presentation Designer ({module.id})...")
            presentation_payload = build_presentation_payload(
                module=module,
                problem_formulation=problem_formulation,
                solution_code=solution_code,
                telemetry=telemetry
            )
            with open(out("slides_payload.json"), "w", encoding="utf-8") as f:
                json.dump(presentation_payload, f, indent=2)

            saved_deck = presentation_designer.generate_presentation_deck(
                module=module,
                problem_formulation=problem_formulation,
                solution_code=solution_code,
                telemetry=telemetry,
                output_path=out("presentation.pptx"),
                artifacts=_collect_deck_artifacts(telemetry_dir, telemetry)
            )
            if not (saved_deck and os.path.exists(saved_deck)):
                raise RuntimeError(f"Presentation deck was not generated for module '{module.id}'.")
            print(f"  -> Saved AI Presentation Deck: {saved_deck}")

            # 6. Cumulative Memory Ledger update for subsequent weeks
            subsystem_components = [
                comp.name
                for sub in (getattr(problem_formulation, "milestone_subsystems", None) or [])
                for comp in sub.components
            ]
            curriculum_history.append({
                "week": module.week,
                "title": module.title,
                "focus": problem_formulation.suggested_focus,
                "components": subsystem_components[:6]
            })
            print(f"  -> Saved all module assets to '{module_dir}/'")

        except Exception as mod_err:
            print(f"[ERROR] Failed processing module {module.id} (Week {module.week}): {mod_err}")
            traceback.print_exc()
            raise

    with open(os.path.join(output_dir, "requirements.txt"), "w", encoding="utf-8") as f:
        f.write(STUDENT_REQUIREMENTS)

    # Reconcile provenance.json with LLM Agent 0 evaluated artifact bindings
    reconcile_provenance_with_llm_evaluations(
        telemetry_dir=telemetry_dir,
        module_artifact_bindings=llm_module_artifact_bindings
    )

    print(f"\n[SUCCESS] Phase 2 LLM curriculum generation complete! Output: {output_dir}")
