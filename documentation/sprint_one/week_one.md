# Phase 1 - Configuration Contract

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
