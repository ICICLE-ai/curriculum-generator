import os
import json
from typing import Optional

from digitalagedu.core.config import load_config
from digitalagedu.core.llm.schemas import (
    Module,
    ProblemStatementSchema,
    SlideDeckSchema,
    ExerciseSolutionSchema,
    UnitTestSchema,
    ValidatedExerciseSchema,
)
from digitalagedu.core.llm.ai_setup import get_instructor_client
from digitalagedu.core.llm.telemetry import load_phase1_telemetry, formulate_problem_statement
from digitalagedu.core.llm.context import (
    build_system_prompt,
    build_slide_prompt,
    build_exercise_prompt,
    build_qa_prompt,
)
from digitalagedu.core.llm.sandbox import run_in_sandbox, clean_code_snippet
from digitalagedu.core.llm.slide_builder import build_pptx_deck

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
    if getattr(curriculum, "modules", None):
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
    elif getattr(curriculum, "topics", None):
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

    # Enforce week sorting
    modules_list.sort(key=lambda m: (m.week if m.week is not None else 999, m.id))

    if not modules_list:
        print("[WARNING] No curriculum modules or topics found in configuration. Exiting Phase 2.")
        return

    for module in modules_list:
        print(f"\n==================================================")
        print(f"Processing LLM Module: {module.title} (Week {module.week})...")
        print(f"==================================================")

        # Agent 0: Problem Formulation
        print(f"0. Agent 0: Formulating problem statement & Markdown overview ({module.id})...")
        problem_formulation: ProblemStatementSchema = formulate_problem_statement(module, telemetry, client, model_name)
        
        overview_path = os.path.join(output_dir, f"{module.id}_overview.md")
        with open(overview_path, "w", encoding="utf-8") as f:
            f.write(problem_formulation.markdown_overview if problem_formulation.markdown_overview else f"# {problem_formulation.title}\n\n{problem_formulation.problem_statement}")
        print(f"  -> Saved Student Overview: {overview_path}")

        # Slide Deck Generation
        print(f"1. Building PowerPoint slide deck for {module.id}...")
        slide_prompt = build_slide_prompt(module, problem_formulation=problem_formulation)
        slide_deck: SlideDeckSchema = client.chat.completions.create(
            model=model_name,
            response_model=SlideDeckSchema,
            max_retries=3,
            max_tokens=4096,
            messages=[
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": slide_prompt}
            ]
        )

        slides_json_path = os.path.join(output_dir, f"{module.id}_slides.json")
        with open(slides_json_path, "w", encoding="utf-8") as f:
            json.dump(slide_deck.model_dump(), f, indent=2)

        pptx_path = os.path.join(output_dir, f"{module.id}_presentation.pptx")
        build_pptx_deck(slide_deck, pptx_path)
        print(f"  -> Saved Widescreen Slide Deck: {pptx_path}")

        # Agent 1: Code Generator
        print(f"2. Agent 1: Synthesizing PyTorch reference solution for {module.id}...")
        exercise_prompt = build_exercise_prompt(module, slide_deck=slide_deck, problem_formulation=problem_formulation)
        solution_result: ExerciseSolutionSchema = client.chat.completions.create(
            model=model_name,
            response_model=ExerciseSolutionSchema,
            max_retries=3,
            max_tokens=4096,
            messages=[
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": exercise_prompt}
            ]
        )

        # Agent 2: Adversarial QA Agent + Sandbox Verification
        print(f"3. Agent 2: Writing unit tests & running Sandbox verification ({module.id})...")
        qa_prompt = build_qa_prompt(module, solution_result.solution_code, problem_formulation=problem_formulation)
        unit_test_result: UnitTestSchema = client.chat.completions.create(
            model=model_name,
            response_model=UnitTestSchema,
            max_retries=3,
            max_tokens=1500,
            messages=[
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": qa_prompt}
            ]
        )

        success, log = run_in_sandbox(solution_result.solution_code, unit_test_result.unit_test)
        if not success:
            print(f"  -> Sandbox verification failed. Triggering Agent 2 self-healing retry...")
            qa_retry_prompt = f"{qa_prompt}\n\n--- PREVIOUS SANDBOX VERIFICATION LOG ---\n{log}\n\nPlease fix the unit_test."
            unit_test_result = client.chat.completions.create(
                model=model_name,
                response_model=UnitTestSchema,
                max_retries=2,
                max_tokens=1500,
                messages=[
                    {"role": "system", "content": build_system_prompt()},
                    {"role": "user", "content": qa_retry_prompt}
                ]
            )
            success, log = run_in_sandbox(solution_result.solution_code, unit_test_result.unit_test)
            if not success:
                print(f"  -> Warning: Final Sandbox Verification Log:\n{log}")

        exercise = ValidatedExerciseSchema.model_construct(
            title=solution_result.title,
            instructions=solution_result.instructions,
            starter_code=solution_result.starter_code,
            solution_code=solution_result.solution_code,
            unit_test=unit_test_result.unit_test
        )

        clean_id = module.id.replace("-", "_")
        json_path = os.path.join(output_dir, f"{module.id}_generated.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(exercise.model_dump(), f, indent=2)

        exercise_path = os.path.join(output_dir, f"{clean_id}_exercise.py")
        with open(exercise_path, "w", encoding="utf-8") as f:
            f.write(f'"""\n{exercise.title}\n\nInstructions:\n{exercise.instructions}\n"""\n\n')
            f.write(clean_code_snippet(exercise.starter_code) + "\n")

        solution_path = os.path.join(output_dir, f"{clean_id}_solution.py")
        with open(solution_path, "w", encoding="utf-8") as f:
            f.write(f'"""\nSolution: {exercise.title}\n"""\n\n')
            f.write(clean_code_snippet(exercise.solution_code) + "\n")

        test_path = os.path.join(output_dir, f"{clean_id}_test.py")
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(f'"""\nUnit Tests: {exercise.title}\n"""\n\n')
            f.write(clean_code_snippet(exercise.unit_test) + "\n")

        print(f"Saved all module assets for {module.id} to '{output_dir}/'")
