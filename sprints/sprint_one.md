# Sprint One: Foundation & Generalization

## Objective
Laying the technical "foundation" of the project by refactoring the core codebase for domain-agnostic execution. This sprint prioritizes architectural integrity and generalizability over new functionality.

---

## Roadmap Overview

| Phase | Focus Area | Deadline | Status |
| :--- | :--- | :--- | :--- |
| **Week 1** | Foundation & Schema Definition | 5/22 | [ ] |
| **Week 2** | Syllabus Refactoring | 5/29 | [ ] |
| **Week 3** | ML Pipeline Decoupling | 6/05 | [ ] |
| **Week 4** | End-to-End Validation | 6/12 | [ ] |

---

## Weekly Detail

### Week 1: Define the Foundation
**Goal:** Lock down the configuration contract to ensure a single source of truth for the entire system.

*   **Deliverables:** Finalized YAML schema, written scope, and project implementation plan.
*   **Focus:** Define schema for dataset paths, class lists, task types, segmentation prompts, and resource links. Document explicit "out-of-scope" items to prevent scope creep.
*   **Implementation Plan:**
    *   [x] Define a comprehensive YAML schema for all pipeline parameters.
    *   [x] Implement flags for environment detection (Local vs. OSC execution).
    *   [x] Draft a formal scope document for Iteration One.

### Week 2: Refactor Syllabus Generation
**Goal:** Prove the curriculum generation side is domain-agnostic.

*   **Deliverables:** Refactored generator, sample non-agriculture syllabus.
*   **Focus:** Eliminate hardcoded agricultural wording and move dataset-specific context into template variables.
*   **Implementation Plan:**
    *   [ ] Add `domain` and `context` fields to the `Topic` model in `config.py`.
    *   [ ] Clean up Jinja2 templates to use generic terminology.
    *   [ ] Generate and verify a curriculum using a non-agricultural dataset (e.g., medical or industrial imagery).

### Week 3: Decouple and Generalize the ML Pipeline
**Goal:** Most critical technical refactor. Replace hardcoded logic with config-driven execution.

*   **Deliverables:** Modular pipeline, dynamic class reading, class-mapping artifacts.
*   **Focus:** Remove agriculture-specific imports and hardcoded task checks. Enable "zero-edit" execution on new labeled datasets.
*   **Implementation Plan:**
    *   [ ] **Dynamic Class Reading:** Replace `KNOWN_CLASSES` with runtime directory scanning.
    *   [ ] **Config-Based Routing:** Refactor `run_pipeline.py` to loop through "tasks" defined in YAML.
    *   [ ] **Decoupling Imports:** Use dynamic loading (e.g., `importlib`) to load task modules by name.
    *   [ ] **Class-Mapping Artifact:** Save a `.json` mapping folders to indices alongside model outputs.

### Week 4: Validate on Test Dataset
**Goal:** End-to-end system verification and performance baseline.

*   **Deliverables:** Full run report, issue log, and follow-up fix list.
*   **Focus:** Capture curriculum and ML outputs. Identify human-in-the-loop requirements and benchmark performance.
*   **Implementation Plan:**
    *   [ ] Execute a full end-to-end run on a small test dataset.
    *   [ ] Document workflow bottlenecks and technical debt.
    *   [ ] Finalize Iteration One and prepare for Iteration Two (Vector DB, etc.).





