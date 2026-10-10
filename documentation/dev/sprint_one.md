# Sprint One - Generalization

## 05/15/2026

The primary goal was to move from a hardcoded, domain-specific script to a generic framework. We established `test_config.yaml` as the central source of truth.

| Component | What | Why |
| :--- | :--- | :--- |
| **Context** | Added `domain` and `context_statement` fields. | Decouples the curriculum generator from agriculture-specific logic. |
| **Orchestration** | Defined `pipeline.stages` as a sequential list. | Replaces hardcoded execution paths with a configurable list of ML tasks. |
| **Resources** | Integrated global `resources` into the schema. | Automates the inclusion of documentation and artifact links in the final syllabus. |
| **Environment** | Added `execution` flags for Local/OSC. | Manages pathing and hardware resource differences between local dev and cluster execution. |

### Class Mapping Artifacts

To ensure reproducibility across datasets regardless of subject, we're implementing a dynamic class mapping field.

* **What:** Automatic generation of a `class_mapping.json` artifact during training/scanning.
* **Why:** Alphabetical folder indexing in `ImageFolder` is unstable across different environments or dataset versions.
* **The Mapping:** A JSON serialized dictionary (e.g., `{"0": "Healthy", "1": "Bacterial_Spot"}`) saved alongside model weights. This allows the inference pipeline to dynamically resolve numerical indices to human-readable labels for any new domain without manual code updates.

## 5/18/2026

The primary goal was to update the core Python logic to ingest the new domain-agnostic YAML config and prove that the curriculum generator functions without domain dependencies.

| Model / Component | What | Why |
| :--- | :--- | :--- |
| **`ProjectModel`** | Added to represent the `project` block. | Captures the domain and context to decouple the generator from agriculture. |
| **`DatasetModel`** | Added to represent the `dataset` block. | Manages dynamic dataset paths and triggers the class mapping generation. |
| **`OutputModel`** | Added to represent the `output` block. | Structures where metrics, models, and outputs are saved. |
| **`PipelineModel`** | Added to represent the `pipeline` block. | Ingests the list of ML tasks to replace hardcoded sequential execution. |
| **`ExecutionModel`** | Added to represent the `execution` block. | Manages pathing and hardware resource differences between local and cluster environments. |
| **`ResourceModel`** | Added to represent external curriculum links. | Automates the inclusion of documentation directly into the syllabus. |
| **Curriculum Service** | Replaced hardcoded "agricultural impact" with `config.project.context_statement`. | Enables dynamic syllabus wording based entirely on the YAML config. |
| **Learning Outcomes** | Fixed `NoneType` bugs for missing optional metadata fields. | Ensures robust parsing when `dataset_metadata` is not yet available. |

### Other Updates

* Updated the Jinja template to include added resources including documentation, links, etc.

* Moved old json outputs into a separate folder

## 5/19/2026

The primary goal was to refactor the ML pipeline orchestrator (`run_pipeline.py`) to be fully domain-agnostic, and to wrap the individual ML modules (Week 8, 9, 10) in standardized interfaces driven entirely by `test_config.yaml`.

| Component | What | Why |
| :--- | :--- | :--- |
| **Dataset Ingestion** | Removed hardcoded dataset paths and static class lists. | Enables dynamic class folder scanning and generic dataset ingestion based on `config.dataset`. |
|JSON Class Mapping|Map each of the classes to an integer saved as `class_mappings.json`|Holds consistancy once retraining or re-running the pipeline. |
| **Module Orchestration** | Replaced static imports with a dynamic `importlib` loop. | Allows the pipeline to execute modules sequentially based on the YAML `pipeline.stages`. |
| **Parameter Generalization** | Pushed execution settings (`batch_size`, `image_size`, `max_samples`) into training scripts. | Decouples model definitions from hardcoded hyperparameters so they are controlled via YAML. |
| **Week 8 Solution** | Added `run_stage` wrapper and dynamic directory creation for PyTorch checkpoints. | Standardizes the interface so `run_pipeline.py` can trigger training and inference uniformly. |

### Other Updates

* Fixed data sampling logic to ignore auto-generated `train/` and `test/` artifact directories to prevent file path crashes.
  * Currently the pipeline reads classes via the data folder (each subfolder is a class), later will be adding an option for test-train-split via the YAML

* Added safety checks for `torch.save` to generate missing parent directories dynamically.

## 5/20/2026

The primary goal today was to generalize the Week 9 SAM module using lazy loading, completely decouple the hardware execution device (CPU vs CUDA) from the code, and evaluate the architectural approach for the final analysis step.

| Component | What | Why |
| :--- | :--- | :--- |
| **Week 9 (SAM)** | Deleted global model instantiation and built a dynamic `get_sam_predictor` lazy loader. | Prevents the 375MB model from crashing the script on import by waiting to load until `run_stage` explicitly calls it. |
| **Device Generalization** | Removed hardcoded global `DEVICE` fallbacks from Week 8 and Week 9. | Allows the pipeline to dynamically swap between local (CPU) and cluster (CUDA) execution via `config.execution.device`. |
| **Week 11 (VLM)** | Drafted an architectural plan to replace hardcoded OpenCV contours with Qwen2-VL. | Replaces dataset-specific algorithms with a generalized Vision Language Model that reads dynamic prompts from the YAML config. |

### Other Updates

* Ran a full pipeline run using the rock-paper-scissors dataset and verified the classification and segmentation stages work perfectly in the local environment.

## 5/21/2026

The primary goal today was to get approval for Moondream2, get access to OSC, and get the csv formatting to accept VQA outputs.

| Component | What | Why |
| :--- | :--- | :--- |
| **Moondream2** | a lightweight VQA model to support generalizable domains and inputs | QA was handled via an OpenCV script hardcoded for plant damage. By using a VQA we can generalize inputs and outputs |
| **CSV Parsing** | Add support for target metric and VQA output | Allows for an organized output of the entire pipeline, including VQA |

## 5/22/2026

The primary goal today was to get the entire pipeline running end to end

| Component | What | Why |
| :--- | :--- | :--- |
| **VQA** | Implemented the final step of the pipeline: VQA | Allows for generalizable input and output rather than static OpenCV scripts |

### Other Updates

* Although the pipeline is running end to end, Moondream is hallucinating a lot. I'll look into this the next day

## 5/23/2026

The primary goal today was to resolve the VLM hallucinations from the previous day, migrate from Moondream to Phi-3-Vision, and successfully execute a flawless local dry run.

| Component | What | Why |
| :--- | :--- | :--- |
| **VLM Replacement** | Swapped Moondream2 for Microsoft's Phi-3-Vision (4B). | Moondream suffered from dependency conflicts with newer `transformers` versions and overflowed in float16, causing severe hallucinations. |
| **Device Execution** | Configured Phi-3 to run natively on GPU (`device_map="cuda"`, `torch_dtype=float16`, `_attn_implementation="eager"`). | Drastically accelerated inference while avoiding hardware crashes on older GPU architectures. |
| **YAML Config Logic** | Fixed the VisionQA YAML configuration to correctly map `prompt` and `target_metric`. | Addressed a bug where the orchestrator fell back to "Describe this image", ensuring the VLM answers the correct question. |
| **Orchestrator Bug** | Fixed a loop indentation bug in `run_pipeline.py`. | Prevented the CSV writer from duplicating results for every stage of the pipeline. |

### Other Updates

* Successfully ran a full, end-to-end dry run (DINOv2 -> SAM -> Phi-3-Vision -> CSV) locally on the GPU. The pipeline architecture is now officially proven and ready for OSC migration!
