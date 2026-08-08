# Implementation Plan: YAML Curriculum Schema & LLM Model Resolution Alignment

This design document outlines the technical plan to align `curriculum_generator`'s YAML schema with `LLM_Curriculum_Testing`'s `test.yaml` format and enable dynamic `model` resolution directly from the `curriculum` block.

## Overview

All changes are 100% backward compatible with existing Phase 1 YAML configs (`skin_cancer_config.yaml`, `sample_config.yaml`, `food_config.yaml`). Phase 1 pipeline execution will continue to work without any breaking changes.

---

## Proposed Technical Changes

### Component 1: Schema Updates (`digitalagedu/core/config.py`)

#### 1. Enhance `CurriculumModuleModel`

Add `title`, `context`, and `difficulty` optional fields to match `test.yaml` module directives:

```python
class CurriculumModuleModel(BaseModel):
    id: str
    week: int = Field(None, ge=1, le=24, description="target week number.")
    weeks: Optional[int] = Field(1, ge=1, le=4, description="Duration in weeks for this module.")
    title: Optional[str] = None
    context: Optional[str] = None
    difficulty: Optional[str] = None
```

#### 2. Enhance `CurriculumConfig`

Add `model` and `target_level`, allow `grade` to accept `Union[int, str]`, and make `topics` default to `[]`:

```python
class CurriculumConfig(BaseModel):
    subject: str
    grade: Optional[Union[int, str]] = Field(10, description="Target grade or academic level")
    target_level: Optional[str] = None
    model: Optional[str] = None # Model to use for generation
    weeks: Optional[int] = Field(
        None, description="Optional number of weeks; if not provided, calculated dynamically if modules provided"
    )

    modules: Optional[List[CurriculumModuleModel]] = None
    topics: List[Topic] = [] # Defaults to empty list for modules-only YAML configs
    resources: Optional[List[ResourceModel]] = None
```

---

### Component 2: Unified Model & Grade Resolution

#### 1. Dynamic Model Resolution (`digitalagedu/core/llm/main.py`)

Update model resolution order to prioritize `curriculum.model`:

```python
    if model_name is None:
        model_name = (
            getattr(root_config.curriculum, "model", None)
            or getattr(root_config.execution, "llm_model", None)
            or getattr(root_config, "model", None)
            or DEFAULT_MODEL_NAME
        )
```

#### 2. SLURM Model Extraction (`cluster_jobs/run_job_vllm.sh`)

Update python inline command to extract `model` from `curriculum` block first:

```bash
MODEL_NAME=$(python -c "import yaml; cfg=yaml.safe_load(open('${CONFIG_FILE}')); print(cfg.get('curriculum', {}).get('model') or cfg.get('execution', {}).get('llm_model') or cfg.get('model') or 'Qwen/Qwen2.5-Coder-32B-Instruct-AWQ')")
```

#### 3. Grade / Academic Level Fallback (`run_pipeline.py` & `orchestrator.py`)

Handle both numeric `grade` and string `target_level`:

```python
grade_str = str(config.curriculum.grade or config.curriculum.target_level or "10").replace(" ", "_").replace("/", "_")
curriculum_md_path = os.path.join(output_dir, f"curriculum_grade_{grade_str}.md")
```

---

### Component 3: Configuration Alignment (`configs/`)

Update `configs/skin_cancer_config.yaml` and `configs/sample_config.yaml` to showcase `model` inside the `curriculum:` block:

```yaml
curriculum:
  subject: "Intro to Medical AI: Skin Cancer Diagnostics"
  target_level: "Undergraduate / Grade 10"
  model: "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ"

  modules:
    - id: "numpy_basics"
      title: "NumPy Basics & Data Structures"
      week: 1
      context: "Perform array calculations and Z-score normalization."
      difficulty: "Beginner"
```

---

## Step-by-Step Execution Sequence

1. **Step 1**: Update `CurriculumModuleModel` and `CurriculumConfig` in `digitalagedu/core/config.py`.
2. **Step 2**: Update model resolution in `digitalagedu/core/llm/main.py`.
3. **Step 3**: Update grade string formatting in `run_pipeline.py` and `digitalagedu/core/orchestrator.py`.
4. **Step 4**: Update model extraction in `cluster_jobs/run_job_vllm.sh`.
5. **Step 5**: Update `configs/skin_cancer_config.yaml` and `configs/sample_config.yaml`.
6. **Step 6**: Run automated Python tests to verify parsing of both `test.yaml` style and `skin_cancer_config.yaml` style configs.

---

## Verification Plan

### Automated Verification

- Verify `load_config('configs/skin_cancer_config.yaml')` correctly parses `curriculum.model`, `title`, `context`, `difficulty`.
- Verify `load_config('test.yaml')` parses `curriculum.target_level` and `curriculum.model` without requiring `topics`.

### Manual Verification

- Run `python run_pipeline.py configs/skin_cancer_config.yaml` to confirm no regressions in output filename generation.
