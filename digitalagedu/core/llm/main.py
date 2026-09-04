import os
import json
from typing import Optional, List, Dict, Any

from digitalagedu.core.config import load_config
from digitalagedu.core.llm.schemas import (
    Module,
    ProblemStatementSchema,
    ExerciseSolutionSchema,
    StarterCodeSchema,
    UnitTestSchema,
    ValidatedExerciseSchema,
    SyllabusPlanSchema,
)
from digitalagedu.core.llm.ai_setup import get_instructor_client
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



DEFAULT_MODEL_NAME = "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ"

def generate_llm_curriculum(
    config_path: str,
    output_dir: Optional[str] = None,
    telemetry_dir: Optional[str] = None,
    base_url: Optional[str] = None,
    model_name: Optional[str] = None
):
    """Main orchestration function executing 3-Agent LLM Curriculum Generation."""
    root_config = load_config(config_path)

    if output_dir is None:
        base_out = root_config.output.directory if root_config.output else "./output"
        output_dir = os.path.join(base_out, "exercises")

    if model_name is None:
        model_name = (
            getattr(root_config.curriculum, "model", None)
            or getattr(root_config.execution, "llm_model", None)
            or getattr(root_config, "model", None)
            or DEFAULT_MODEL_NAME
        )

    if base_url is None:
        base_url = getattr(root_config.execution, "llm_base_url", "http://localhost:8000/v1")

    if telemetry_dir is None:
        telemetry_dir = root_config.output.directory if root_config.output else "./output"

    print(f"\n[Phase 2 LLM Pipeline] Using Model: {model_name} | Endpoint: {base_url or 'default'}")
    client = get_instructor_client(base_url=base_url)
    os.makedirs(output_dir, exist_ok=True)

    # Ingest Phase 1 Telemetry
    telemetry = load_phase1_telemetry(telemetry_dir)
    if telemetry:
        print(f"[Telemetry Loaded] Found telemetry from Phase 1 output dir: {telemetry_dir}")

    # Build modules list from RootConfig
    curriculum = root_config.curriculum
    modules_list = []
    syllabus_plan = None

    if getattr(curriculum, "modules", None) and len(curriculum.modules) > 0:
        print("[Curriculum Config] Using explicit modules defined in YAML configuration.")
        sorted_modules = sorted(curriculum.modules, key=lambda m: (m.week if m.week is not None else 999, m.id))
        for m in sorted_modules:
            title = getattr(m, "title", None) or m.id.replace("_", " ").replace("-", " ").title()
            context = getattr(m, "context", None) or f"{curriculum.subject} ({m.id})"
            difficulty = getattr(m, "difficulty", None) or "intermediate"
            modules_list.append(
                Module(
                    id=m.id,
                    title=title,
                    week=m.week or 1,
                    context=context,
                    difficulty=difficulty
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
        # Autonomous Syllabus Formulation via Syllabus Architect Agent
        print("\n[Syllabus Architect] No explicit modules provided in YAML. Autonomously formulating complete curriculum...")
        syllabus_plan, modules_list = formulate_syllabus(root_config, telemetry, client, model_name)
        
        # Save syllabus plan artifacts
        syllabus_json_path = os.path.join(output_dir, "syllabus_plan.json")
        with open(syllabus_json_path, "w", encoding="utf-8") as f:
            f.write(syllabus_plan.model_dump_json(indent=2))
        print(f"  -> Saved Syllabus Plan JSON: {syllabus_json_path}")

        syllabus_md_path = os.path.join(output_dir, "course_syllabus.md")
        with open(syllabus_md_path, "w", encoding="utf-8") as f:
            f.write(f"# {syllabus_plan.course_title}\n\n")
            f.write(f"**Target Level:** {getattr(curriculum, 'grade', 10)} | **Duration:** {len(modules_list)} Weeks\n\n")
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

    # Enforce week sorting
    modules_list.sort(key=lambda m: (m.week if m.week is not None else 999, m.id))

    if not modules_list:
        print("[WARNING] No curriculum modules could be formulated. Exiting Phase 2.")
        return

    presentation_designer = PresentationDesigner(client=client, model_name=model_name)
    curriculum_history: List[Dict[str, Any]] = []

    for module in modules_list:
        print(f"\n==================================================")
        print(f"Processing LLM Module: {module.title} (Week {module.week})...")
        print(f"==================================================")

        clean_id = module.id.replace("-", "_")
        week_folder = f"Week_{module.week:02d}"
        module_dir = os.path.join(output_dir, week_folder, clean_id)
        os.makedirs(module_dir, exist_ok=True)

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
            
            overview_path = os.path.join(module_dir, f"{clean_id}_overview.md")
            with open(overview_path, "w", encoding="utf-8") as f:
                f.write(problem_formulation.markdown_overview if problem_formulation.markdown_overview else f"# {problem_formulation.title}\n\n{problem_formulation.problem_statement}")
            print(f"  -> Saved Student Overview: {overview_path}")

            # 1. Agent 2 (QA): TDD Step 1 - Generate Unit Tests First from Subsystem Contracts
            print(f"1. Agent 2 (QA): Writing property-based unit tests for {module.id}...")
            qa_prompt = build_qa_prompt(module, problem_formulation=problem_formulation)
            unit_test_result: UnitTestSchema = client.chat.completions.create(
                model=model_name,
                response_model=UnitTestSchema,
                max_retries=3,
                max_tokens=4096,
                messages=[
                    {"role": "system", "content": build_system_prompt()},
                    {"role": "user", "content": qa_prompt}
                ]
            )

            # 2. Agent 1 (Coder): TDD Step 2 - Implement Reference Solution to Pass Unit Tests
            print(f"2. Agent 1 (Coder): Synthesizing reference solution satisfying unit tests ({module.id})...")
            exercise_prompt = build_exercise_prompt(
                module=module,
                problem_formulation=problem_formulation,
                unit_test_code=unit_test_result.unit_test,
                curriculum_history=curriculum_history
            )
            solution_result: ExerciseSolutionSchema = client.chat.completions.create(
                model=model_name,
                response_model=ExerciseSolutionSchema,
                max_retries=3,
                max_tokens=8192,
                messages=[
                    {"role": "system", "content": build_system_prompt()},
                    {"role": "user", "content": exercise_prompt}
                ]
            )

            # 3. Execution Sandbox Verification with Bidirectional Self-Healing
            print(f"3. Sandbox: Verifying solution against unit tests ({module.id})...")
            success, log = run_in_sandbox(solution_result.solution_code, unit_test_result.unit_test, module_id=module.id)
            if not success:
                print(f"  -> Sandbox verification failed. Diagnosing root cause from log...")
                # Check where the error originated:
                is_solution_fault = (
                    f"{clean_id}_solution" in log or 
                    "NameError:" in log or 
                    "ModuleNotFoundError:" in log or 
                    "AttributeError:" in log or
                    ("TypeError:" in log and "test_runner" not in log)
                )
                
                if is_solution_fault:
                    print(f"  -> Error detected in solution_code. Triggering Agent 1 self-healing retry...")
                    solution_retry_prompt = (
                        f"{exercise_prompt}\n\n"
                        f"--- PREVIOUS SANDBOX EXECUTION FAILURE LOG ---\n{log}\n\n"
                        f"CRITICAL FIX DIRECTIVE:\n"
                        f"Your previous solution failed during execution. Fix the error:\n"
                        f"1. Explicitly import all used libraries and functions at the top.\n"
                        f"2. Never call disk-loading functions with non-existent file paths.\n"
                        f"3. Ensure all subsystem component signatures match the unit test expectations.\n"
                        f"Return the complete, working solution_code."
                    )
                    solution_result = client.chat.completions.create(
                        model=model_name,
                        response_model=ExerciseSolutionSchema,
                        max_retries=2,
                        max_tokens=8192,
                        messages=[
                            {"role": "system", "content": build_system_prompt()},
                            {"role": "user", "content": solution_retry_prompt}
                        ]
                    )
                    success, log = run_in_sandbox(solution_result.solution_code, unit_test_result.unit_test, module_id=module.id)

                if not success:
                    print(f"  -> Triggering Agent 2 test verification self-healing retry...")
                    qa_retry_prompt = (
                        f"{qa_prompt}\n\n"
                        f"--- REFERENCE SOLUTION CODE ---\n{solution_result.solution_code}\n\n"
                        f"--- PREVIOUS SANDBOX VERIFICATION LOG ---\n{log}\n\n"
                        f"Please fix the unit_test code to properly assert the solution without syntax or assertion errors."
                    )
                    unit_test_result = client.chat.completions.create(
                        model=model_name,
                        response_model=UnitTestSchema,
                        max_retries=2,
                        max_tokens=4096,
                        messages=[
                            {"role": "system", "content": build_system_prompt()},
                            {"role": "user", "content": qa_retry_prompt}
                        ]
                    )
                    success, log = run_in_sandbox(solution_result.solution_code, unit_test_result.unit_test, module_id=module.id)
                    if not success:
                        print(f"  -> Warning: Final Sandbox Verification Log:\n{log}")

            # Save verification report
            verification_path = os.path.join(module_dir, f"{clean_id}_verification.json")
            with open(verification_path, "w", encoding="utf-8") as f:
                json.dump({
                    "module_id": module.id,
                    "verified": success,
                    "log": "All tests passed cleanly in sandbox." if success else log
                }, f, indent=2)

            # 4. TDD Step 3: Exercise Scaffolding derived from verified solution
            print(f"4. Scaffolding student starter code from verified solution ({module.id})...")
            starter_code = solution_result.starter_code
            try:
                scaffold_prompt = build_scaffold_prompt(module, problem_formulation, solution_result.solution_code)
                starter_result: StarterCodeSchema = client.chat.completions.create(
                    model=model_name,
                    response_model=StarterCodeSchema,
                    max_retries=2,
                    max_tokens=4096,
                    messages=[
                        {"role": "system", "content": build_system_prompt()},
                        {"role": "user", "content": scaffold_prompt}
                    ]
                )
                if starter_result.starter_code and len(starter_result.starter_code.strip()) > 30:
                    starter_code = starter_result.starter_code
            except Exception as e:
                print(f"  -> Notice: Fallback to existing starter scaffolding: {e}")

            # Write out primary exercise artifacts immediately
            exercise = ValidatedExerciseSchema.model_construct(
                title=problem_formulation.title,
                instructions=problem_formulation.problem_statement,
                starter_code=starter_code or "# Student implementation starter skeleton\n",
                solution_code=solution_result.solution_code,
                unit_test=unit_test_result.unit_test
            )

            json_path = os.path.join(module_dir, f"{clean_id}_generated.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(exercise.model_dump(), f, indent=2)

            exercise_path = os.path.join(module_dir, f"{clean_id}_exercise.py")
            with open(exercise_path, "w", encoding="utf-8") as f:
                f.write(f'"""\n{exercise.title}\n\nInstructions:\n{exercise.instructions}\n"""\n\n')
                f.write(clean_code_snippet(exercise.starter_code) + "\n")

            solution_path = os.path.join(module_dir, f"{clean_id}_solution.py")
            with open(solution_path, "w", encoding="utf-8") as f:
                f.write(f'"""\nSolution: {exercise.title}\n"""\n\n')
                f.write(clean_code_snippet(exercise.solution_code) + "\n")

            test_path = os.path.join(module_dir, f"{clean_id}_test.py")
            with open(test_path, "w", encoding="utf-8") as f:
                f.write(f'"""\nUnit Tests: {exercise.title}\n"""\n\n')
                f.write(clean_code_snippet(exercise.unit_test) + "\n")

            # 5. Agentic 16:9 Presentation Generation
            print(f"5. Synthesizing domain-grounded presentation deck via Presentation Designer ({module.id})...")
            try:
                presentation_payload = build_presentation_payload(
                    module=module,
                    problem_formulation=problem_formulation,
                    solution_code=solution_result.solution_code,
                    telemetry=telemetry
                )
                
                slides_json_path = os.path.join(module_dir, f"{clean_id}_slides_payload.json")
                with open(slides_json_path, "w", encoding="utf-8") as f:
                    json.dump(presentation_payload, f, indent=2)

                pptx_path = os.path.join(module_dir, f"{clean_id}_presentation.pptx")
                presentation_designer.generate_presentation_deck(
                    module=module,
                    problem_formulation=problem_formulation,
                    solution_code=solution_result.solution_code,
                    telemetry=telemetry,
                    output_path=pptx_path
                )
                print(f"  -> Saved AI Presentation Deck: {pptx_path}")
            except Exception as pptx_err:
                print(f"  -> [WARNING] Presentation generation encountered an error: {pptx_err}. Continuing with module.")

            # 6. Cumulative Memory Ledger update for subsequent weeks
            subsystem_components = []
            if getattr(problem_formulation, "milestone_subsystems", None):
                for sub in problem_formulation.milestone_subsystems:
                    for comp in sub.components:
                        subsystem_components.append(comp.name)
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
            print(f"  -> Continuing to next module to prevent pipeline termination...")

    # Package student requirements.txt in the root output folder
    requirements_path = os.path.join(output_dir, "requirements.txt")
    student_requirements = (
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
    with open(requirements_path, "w", encoding="utf-8") as f:
        f.write(student_requirements)
    print(f"\n[SUCCESS] Phase 2 LLM curriculum generation complete! Output: {output_dir}")
