# Implementation Plan: Phase 2 LLM Integration into `DigitalAgEdu`

This design document outlines the step-by-step technical plan to port the autonomous 3-agent LLM curriculum generation framework (`LLM_Curriculum_Testing`) into `curriculum_generator`.

## Overview

The LLM generation code operates purely via HTTP REST API (`openai` / `instructor` targeting `vLLM` on `localhost:8000`). It introduces zero GPU memory conflicts with Phase 1 PyTorch models during pipeline runs.

---

## Proposed Technical Changes

### Component 1: Package Structure & Subpackage Creation (`digitalagedu/core/llm`)

Port the core modules from `LLM_Curriculum_Testing/core/` into a dedicated subpackage inside `digitalagedu/core/llm/`.

#### [NEW] [digitalagedu/core/llm/__init__.py](file:///c:/Desktop/Coding%20Projects/curriculum_generator/digitalagedu/core/llm/__init__.py)

Exposes the master `generate_llm_curriculum` entrypoint function.

#### [NEW] [digitalagedu/core/llm/ai_setup.py](file:///c:/Desktop/Coding%20Projects/curriculum_generator/digitalagedu/core/llm/ai_setup.py)

Configures `Instructor` client targeting local/remote vLLM endpoints.

#### [NEW] [digitalagedu/core/llm/telemetry.py](file:///c:/Desktop/Coding%20Projects/curriculum_generator/digitalagedu/core/llm/telemetry.py)

Ingests Phase 1 outputs (`results.csv`, `run_summary.json`, `class_mapping.json`, `cv_report.json`) and extracts the __Universal 4-Sample Contrastive Matrix__ (*Top Success*, *Hard Failure*, *Boundary Uncertainty*, *Minority Sample*).

#### [NEW] [digitalagedu/core/llm/context.py](file:///c:/Desktop/Coding%20Projects/curriculum_generator/digitalagedu/core/llm/context.py)

Agent 0 (Problem Formulation), Agent 1 (Code Educator), and Agent 2 (Adversarial QA) prompt builders + RAG vector store queries.

#### [NEW] [digitalagedu/core/llm/slide_builder.py](file:///c:/Desktop/Coding%20Projects/curriculum_generator/digitalagedu/core/llm/slide_builder.py)

Headless `python-pptx` 16:9 widescreen PowerPoint deck builder.

#### [NEW] [digitalagedu/core/llm/sandbox.py](file:///c:/Desktop/Coding%20Projects/curriculum_generator/digitalagedu/core/llm/sandbox.py)

Subprocess sandbox execution harness with automated self-healing diagnostic feedback loop.

#### [NEW] [digitalagedu/core/llm/schemas/generation_types.py](file:///c:/Desktop/Coding%20Projects/curriculum_generator/digitalagedu/core/llm/schemas/generation_types.py)

Pydantic v2 schemas (`ProblemStatementSchema`, `SlideDeckSchema`, `ExerciseSolutionSchema`, `UnitTestSchema`, `ValidatedExerciseSchema`).

#### [NEW] [digitalagedu/core/llm/schemas/module_types.py](file:///c:/Desktop/Coding%20Projects/curriculum_generator/digitalagedu/core/llm/schemas/module_types.py)

Pydantic v2 `Module` schema mapping curriculum topic directives.

#### [NEW] [digitalagedu/core/llm/main.py](file:///c:/Desktop/Coding%20Projects/curriculum_generator/digitalagedu/core/llm/main.py)

Master orchestration loop executing Agent 0 -> Slide Deck -> Agent 1 -> Agent 2 Sandbox -> Asset exporter (`{id}_overview.md`, `{id}_presentation.pptx`, `{id}_exercise.py`, `{id}_solution.py`, `{id}_test.py`, `{id}_generated.json`).

---

### Component 2: Configuration & Engine Extensions

#### [MODIFY] [digitalagedu/core/config.py](file:///c:/Desktop/Coding%20Projects/curriculum_generator/digitalagedu/core/config.py)

Add Phase 2 LLM execution fields to `ExecutionModel`:

```python
class ExecutionModel(BaseModel):
    ...
    # --- Phase 2 LLM Setup ---
    use_llm: Optional[bool] = False
    llm_base_url: Optional[str] = "http://localhost:8000/v1"
    llm_model: Optional[str] = "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ"
```

#### [MODIFY] [digitalagedu/core/__init__.py](file:///c:/Desktop/Coding%20Projects/curriculum_generator/digitalagedu/core/__init__.py)

Re-export `generate_llm_curriculum` from `digitalagedu.core.llm`.

#### [MODIFY] [configs/skin_cancer_config.yaml](file:///c:/Desktop/Coding%20Projects/curriculum_generator/configs/skin_cancer_config.yaml) & [configs/sample_config.yaml](file:///c:/Desktop/Coding%20Projects/curriculum_generator/configs/sample_config.yaml)

Add `use_llm`, `llm_base_url`, and `llm_model` configuration defaults.

---

### Component 3: Pipeline Integration

#### [MODIFY] [run_pipeline.py](file:///c:/Desktop/Coding%20Projects/curriculum_generator/run_pipeline.py)

Add conditional trigger after Phase 1 metrics report generation:

```python
    if getattr(config.execution, "use_llm", False):
        print("\n[INFO] Triggering Phase 2 LLM Autonomous Curriculum Generation...")
        from digitalagedu.core.llm import generate_llm_curriculum
        generate_llm_curriculum(
            config_path=config_path,
            output_dir=os.path.join(output_dir, "llm_artifacts"),
            telemetry_dir=output_dir,
            base_url=getattr(config.execution, "llm_base_url", "http://localhost:8000/v1"),
            model_name=getattr(config.execution, "llm_model", "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ")
        )
```

---

## Step-by-Step Execution Sequence

1. __Step 1__: Create directory `digitalagedu/core/llm/` and `digitalagedu/core/llm/schemas/`.
2. __Step 2__: Write `digitalagedu/core/llm/schemas/generation_types.py` and `module_types.py`.
3. __Step 3__: Write `digitalagedu/core/llm/ai_setup.py`, `telemetry.py`, `sandbox.py`, and `slide_builder.py`.
4. __Step 4__: Write `digitalagedu/core/llm/context.py` and `main.py`.
5. __Step 5__: Export `generate_llm_curriculum` in `digitalagedu/core/llm/__init__.py` and `digitalagedu/core/__init__.py`.
6. __Step 6__: Update `ExecutionModel` in `digitalagedu/core/config.py` and sample YAML configs in `configs/`.
7. __Step 7__: Update `run_pipeline.py` to trigger Phase 2 when `use_llm: true`.

---

## Verification Plan

### Automated Verification

- Verify module imports cleanly: `python -c "import digitalagedu.core.llm; print('LLM module import OK')"`
- Run `pytest` / unit check on config loading with `use_llm: true`.

### Manual Verification

- Test Phase 2 telemetry loading against existing `verified_outputs/` directory.
- Verify slide builder produces a valid `.pptx` presentation deck.
- Verify sandbox test execution function `run_in_sandbox` cleanly runs synthetic PyTorch tensor code.
