# Sprint Two - Verification and Model Validation

## Overview

Following the successful deployment of the AI pipeline across multiple domains on the Ohio Supercomputer Center (OSC), the primary goal of Sprint Two shifts from operational execution ("can it run?") to output dependability ("can we trust its outputs and learning alignment?"). This sprint focuses on validating model accuracy, debugging prediction mismatches, and establishing robust reporting to ensure the pipeline acts as a polished, reliable curriculum tool.

## Objectives & Action Items

### 1. Advanced Evaluation Protocol

- **Confusion Matrices:** Generate and save confusion matrices for both the Skin Cancer and Hurricane tasks to visually represent error distribution.

### 2. Deep Error Analysis & Medical Relevance

- **Manual Row Audit:** Conduct a small manual audit of randomly selected rows to explicitly confirm that `predicted_class` is truly the model output and the explanatory fields are functioning strictly as support.
- **Sensitivity & False Negative Tracking:** For the Skin Cancer task, explicitly report sensitivity and the false-negative rate alongside raw accuracy, as false negatives carry extreme medical weight.
- **Imbalance Discussions:** For the Hurricane task, discuss and document class imbalance and error direction, noting how these metrics impact real-world interpretation.

### 3. Deliverable: The Reproducible Evaluation Package

- **Final Output Generation:** Assemble a tangible evaluation package for Prof. Hari. This package must include:
  - The final Result CSVs.
  - The newly enriched JSON summaries (containing Precision, Recall, F1, FN, FP, and Metadata).
  - The generated Confusion Matrices.
  - A short written Methods/Results document explaining the evaluation setup and main findings.

### 4. Completed Objectives

- **Stratified 5-Fold Cross-Validation:** Locked the evaluation protocol and implemented stratified 5-fold CV to prove the model's stability across different data splits.
- **Validation Loss Tracking:** Updated training scripts to track validation loss carefully, ensuring the best model is saved based on validation performance (not training performance).
- **Metadata Recording:** Updated the YAML schema, PyDantic models, and `run_summary.json` to lock and record exact run metadata (specifically the random seed).
- **Schema Verification:** Successfully decoupled DINOv2 predictions from VLM outputs, confirming the column semantics.
- **Metrics Module:** Built `metrics.py` to automatically calculate Precision, Recall, F1, False Positives, and False Negatives.
- **Scale Up Validation Runs:** Successfully executed 1,000-row runs on the OSC cluster for both Hurricane (94.5% accuracy) and Skin Cancer (86.2% accuracy).
