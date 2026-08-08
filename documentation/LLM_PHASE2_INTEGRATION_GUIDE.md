# Step-by-Step Implementation Guide: Integrating Phase 2 LLM Curriculum Generation into `DigitalAgEdu`

> **Document Version:** 1.0  
> **Target Branch:** `iteration_three`  
> **Status:** Implementation Guide  

---

## 1. Overview & System Synergy

The goal of Phase 2 is to take the raw execution telemetry produced by Phase 1 (`results.csv`, `run_summary.json`, `class_mapping.json`) and autonomously synthesize:

1. **Student Concept & Domain Overview Documents** (`.md`)
2. **Widescreen Presentation Slide Decks** (`.pptx`)
3. **Student Starter Skeleton Code** (`.py`)
4. **Verified PyTorch Reference Solutions** (`.py`)
5. **Standalone Property-Based Unit Test Suites** (`.py`)
6. **Structured Module Metadata Payloads** (`.json`)

---

## 2. Step-by-Step Integration Plan

### Step 1: Create the Subpackage `digitalagedu/core/llm`

Port the modules from `LLM_Curriculum_Testing/core/` into `digitalagedu/core/llm/`:

```
digitalagedu/
└── core/
    ├── config.py
    ├── curriculum_service.py
    ├── practice_generator.py
    └── llm/                             # NEW SUBPACKAGE
        ├── __init__.py
        ├── ai_setup.py                  # Instructor vLLM client builder
        ├── context.py                   # Agent 0, 1, 2 system prompts
        ├── telemetry.py                 # Phase 1 telemetry parser & 4-sample matrix
        ├── sandbox.py                   # Subprocess sandbox with self-healing retries
        ├── slide_builder.py             # python-pptx widescreen slide deck generator
        ├── main.py                      # Phase 2 master generator runner
        └── schemas/                     # Pydantic v2 schemas
            ├── __init__.py
            ├── generation_types.py
            └── module_types.py
```

---

### Step 2: Extend Configuration Schema (`digitalagedu/core/config.py`)

Update `ExecutionModel` in `digitalagedu/core/config.py` to support LLM execution flags:

```python
class ExecutionModel(BaseModel):
    environment: Optional[str] = None
    device: str
    batch_size: int
    image_size: int
    max_samples: Optional[int] = None
    seed: Optional[int] = None
    
    # --- W&B Setup ---
    use_wandb: Optional[bool] = False
    use_profiler: Optional[bool] = False
    wandb_project: Optional[str] = "digitalagedu"

    # --- Phase 2 LLM Setup ---
    use_llm: Optional[bool] = False
    llm_base_url: Optional[str] = "http://localhost:8000/v1"
    llm_model: Optional[str] = "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ"
```

In your YAML configuration files (e.g. `skin_cancer_config.yaml`), add:

```yaml
execution:
  device: "cuda"
  batch_size: 16
  image_size: 518
  
  # Enable Phase 2 LLM generation
  use_llm: true
  llm_base_url: "http://localhost:8000/v1"
  llm_model: "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ"
```

---

### Step 3: Connect Pipeline Entrypoint (`run_pipeline.py`)

At the end of `run_pipeline.py` (after Phase 1 metrics report generation), add the Phase 2 execution trigger:

```python
    # -------------------------------------------------------------
    # Phase 2: Autonomous LLM Curriculum Generation (Optional)
    # -------------------------------------------------------------
    if getattr(config.execution, "use_llm", False):
        print("\n[INFO] Triggering Phase 2 LLM Autonomous Curriculum Generation...")
        try:
            from digitalagedu.core.llm.main import generate_llm_curriculum
            llm_output_dir = os.path.join(output_dir, "llm_artifacts")
            generate_llm_curriculum(
                config_path=config_path,
                output_dir=llm_output_dir,
                telemetry_dir=output_dir,
                base_url=config.execution.llm_base_url,
                model_name=config.execution.llm_model
            )
            print(f"[SUCCESS] LLM Curriculum Assets saved to {llm_output_dir}")
        except Exception as e:
            print(f"[WARNING] Phase 2 LLM Generation failed: {e}")
```

---

### Step 4: Execute Job on OSC (`run_job_vllm.sh`)

Use the updated single-job SLURM submission script on OSC:

```bash
sbatch run_job_vllm.sh skin_cancer_config.yaml
```

The script will automatically:

1. Load `python/3.10` and `cuda/12.1.1` to run Phase 1.
2. Terminate Phase 1 and deactivate Python to release 100% of GPU VRAM.
3. Unload Phase 1 modules and load `vllm/0.23.0`.
4. Spin up the local `vLLM` server on `http://localhost:8000/v1`.
5. Execute Phase 2 LLM Curriculum Generation.
6. Clean up the background `vLLM` server process upon completion.

---

## 3. Output Artifact Directory Layout

Phase 2 will generate the following deliverables inside `output/skin_cancer_v1/llm_artifacts/`:

```
output/skin_cancer_v1/llm_artifacts/
├── {module_id}_overview.md        # Student Markdown concept overview
├── {module_id}_presentation.pptx  # 16:9 widescreen PowerPoint deck
├── {module_id}_slides.json        # Slide deck JSON metadata
├── {module_id}_exercise.py        # Student starter skeleton code
├── {module_id}_solution.py        # Verified reference PyTorch solution
├── {module_id}_test.py            # Standalone property unit test harness
└── {module_id}_generated.json     # Complete module metadata payload
```

---

## 4. Verification & Testing Checklist

- [x] Dependencies added to `requirements.txt`.
- [x] SLURM script `run_job_vllm.sh` updated for mid-job module switching.
- [ ] Port `LLM_Curriculum_Testing/core/` into `digitalagedu/core/llm/`.
- [ ] Update `ExecutionModel` in `digitalagedu/core/config.py`.
- [ ] Add Phase 2 trigger to `run_pipeline.py`.
- [ ] Run test execution on OSC Ascend (`sbatch run_job_vllm.sh skin_cancer_config.yaml`).
