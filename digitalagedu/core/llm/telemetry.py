import os
import json
import csv
from typing import Dict, Any, List, Optional
import instructor
from digitalagedu.core.llm.schemas import ProblemStatementSchema

def extract_contrastive_samples(rows: List[Dict[str, Any]]) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Extracts 4 domain-agnostic contrastive samples based on universal statistical properties:
    1. top_success: High-confidence correct prediction
    2. hard_failure: Misclassified failure case
    3. boundary_uncertainty: Sample nearest to decision boundary
    4. minority_sample: Representative sample from least frequent class
    """
    if not rows:
        return {}

    gt_col = next((c for c in ["ground_truth", "target", "label", "y_true"] if c in rows[0]), None)
    pred_col = next((c for c in ["predicted_class", "prediction", "y_pred"] if c in rows[0]), None)
    prob_col = next((c for c in ["probabilities", "score", "confidence", "probability"] if c in rows[0]), None)

    samples = {
        "top_success": None,
        "hard_failure": None,
        "boundary_uncertainty": None,
        "minority_sample": None
    }

    if not (gt_col and pred_col):
        samples["top_success"] = rows[0]
        if len(rows) > 1:
            samples["hard_failure"] = rows[1]
        return samples

    def get_max_prob(row):
        val = row.get(prob_col, "")
        if isinstance(val, str) and val.startswith("["):
            try:
                probs = json.loads(val)
                return max(probs)
            except Exception:
                return 0.5
        try:
            return float(val)
        except Exception:
            return 0.5

    # 1. Hard Failure
    failures = [r for r in rows if r.get(gt_col) != r.get(pred_col)]
    if failures:
        samples["hard_failure"] = max(failures, key=get_max_prob)
    elif len(rows) > 1:
        samples["hard_failure"] = rows[1]

    # 2. Top Success
    successes = [r for r in rows if r.get(gt_col) == r.get(pred_col)]
    if successes:
        samples["top_success"] = max(successes, key=get_max_prob)
    else:
        samples["top_success"] = rows[0]

    # 3. Boundary Uncertainty
    samples["boundary_uncertainty"] = min(rows, key=lambda r: abs(get_max_prob(r) - 0.5))

    # 4. Minority Sample
    class_counts = {}
    for r in rows:
        gt = r.get(gt_col)
        class_counts[gt] = class_counts.get(gt, 0) + 1
    if class_counts:
        minority_gt = min(class_counts, key=lambda k: class_counts[k])
        minority_rows = [r for r in rows if r.get(gt_col) == minority_gt]
        if minority_rows:
            samples["minority_sample"] = minority_rows[0]

    return samples

def load_phase1_telemetry(telemetry_dir: str = "output") -> Dict[str, Any]:
    """Reads all Phase 1 telemetry JSON and CSV files from the specified folder."""
    telemetry = {}
    if not os.path.exists(telemetry_dir):
        return telemetry

    # 1. Class Mapping
    class_map_path = os.path.join(telemetry_dir, "class_mapping.json")
    if os.path.exists(class_map_path):
        try:
            with open(class_map_path, "r", encoding="utf-8") as f:
                telemetry["class_mapping"] = json.load(f)
        except Exception:
            pass

    # 2. Run Summary
    run_summary_path = os.path.join(telemetry_dir, "run_summary.json")
    if os.path.exists(run_summary_path):
        try:
            with open(run_summary_path, "r", encoding="utf-8") as f:
                telemetry["run_summary"] = json.load(f)
        except Exception:
            pass

    # 3. Cross-Validation Report
    cv_report_path = os.path.join(telemetry_dir, "cv_report.json")
    if os.path.exists(cv_report_path):
        try:
            with open(cv_report_path, "r", encoding="utf-8") as f:
                telemetry["cv_report"] = json.load(f)
        except Exception:
            pass

    # 4. CSV Statistical Contrastive Sample Extraction
    results_csv_path = os.path.join(telemetry_dir, "results.csv")
    if os.path.exists(results_csv_path):
        try:
            with open(results_csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                all_rows = [next(reader) for _ in range(50)]
                telemetry["contrastive_samples"] = extract_contrastive_samples(all_rows)
                telemetry["artifact_columns"] = list(all_rows[0].keys()) if all_rows else []
        except Exception:
            pass

    # 5. Authentic Image Assets
    images_dir = os.path.join(telemetry_dir, "images")
    raw_dir = os.path.join(images_dir, "raw")
    mask_dir = os.path.join(images_dir, "masks")
    dataset_sample_dir = os.path.join(images_dir, "dataset_sample")

    sample_img_name = None
    if os.path.exists(raw_dir):
        raw_files = [f for f in os.listdir(raw_dir) if not f.startswith(".")]
        if raw_files:
            sample_img_name = raw_files[0]

    sample_mask_name = None
    if os.path.exists(mask_dir):
        mask_files = [f for f in os.listdir(mask_dir) if not f.startswith(".")]
        if mask_files:
            sample_mask_name = mask_files[0]

    sample_classes = []
    if os.path.exists(dataset_sample_dir):
        sample_classes = [d for d in os.listdir(dataset_sample_dir) if os.path.isdir(os.path.join(dataset_sample_dir, d))]

    if os.path.exists(dataset_sample_dir) or sample_img_name:
        telemetry["image_assets"] = {
            "dataset_sample_rel_path": "../../../images/dataset_sample",
            "raw_sample_rel_path": f"../../../images/raw/{sample_img_name}" if sample_img_name else None,
            "mask_sample_rel_path": f"../../../images/masks/{sample_mask_name}" if sample_mask_name else None,
            "results_csv_rel_path": "../../../results.csv",
            "available_classes": sample_classes
        }

    return telemetry

def build_telemetry_prompt_summary(telemetry: Dict[str, Any]) -> str:
    """Formats raw Phase 1 telemetry dict into a clean prompt context string for Agent 0."""
    if not telemetry:
        return "No Phase 1 pipeline telemetry available. Use generic computing context."

    summary_lines = ["--- PHASE 1 PIPELINE TELEMETRY ---"]
    
    if "run_summary" in telemetry:
        rs = telemetry["run_summary"]
        summary_lines.append(f"Dataset/Config: {rs.get('config_file', 'dataset')}")
        summary_lines.append(f"Total Rows Processed: {rs.get('total_rows_processed', 'N/A')}")
        summary_lines.append(f"Overall Accuracy: {rs.get('overall_accuracy_percent', 'N/A')}% | AUC-ROC: {rs.get('auc_roc', 'N/A')}")
        summary_lines.append(f"Class Balance: {rs.get('class_balance', {})}")
        summary_lines.append(f"Error Telemetry: {rs.get('error_counts', {})}")
        summary_lines.append(f"Per-Class Metrics: {rs.get('metrics_per_class', {})}")

    if "class_mapping" in telemetry:
        summary_lines.append(f"Class Labels: {telemetry['class_mapping']}")

    if "cv_report" in telemetry:
        cv = telemetry["cv_report"]
        summary_lines.append(f"5-Fold CV Mean Accuracy: {cv.get('mean_accuracy', 'N/A')} | Mean F1: {cv.get('mean_f1', 'N/A')}")

    if "artifact_columns" in telemetry:
        summary_lines.append(f"Pipeline Artifact Columns: {telemetry['artifact_columns']}")

    if "contrastive_samples" in telemetry and telemetry["contrastive_samples"]:
        summary_lines.append("\n--- STATISTICAL CONTRASTIVE SAMPLES (AGENT 0 REFERENCE) ---")
        for category, sample in telemetry["contrastive_samples"].items():
            if sample:
                summary_lines.append(f"[{category.upper()} SAMPLE]: {sample}")

    if "image_assets" in telemetry:
        ia = telemetry["image_assets"]
        summary_lines.append("\n--- AUTHENTIC LAB DATASET ASSETS (RELATIVE PATHS FROM EXERCISE) ---")
        summary_lines.append(f"- Sample Dataset Directory: `{ia.get('dataset_sample_rel_path')}` (organized by class subfolders)")
        if ia.get("raw_sample_rel_path"):
            summary_lines.append(f"- Representative Raw Sample Image: `{ia.get('raw_sample_rel_path')}`")
        if ia.get("mask_sample_rel_path"):
            summary_lines.append(f"- Paired Segmentation Mask: `{ia.get('mask_sample_rel_path')}`")
        summary_lines.append(f"- Pipeline Results CSV: `{ia.get('results_csv_rel_path')}`")
        summary_lines.append("- Portable Access Pattern: Code should attempt to load from these relative paths when present, with a graceful synthetic in-memory fallback for isolated testing environments.")

    return "\n".join(summary_lines)

def formulate_problem_statement(
    module, 
    telemetry: Dict[str, Any], 
    client: instructor.Instructor, 
    model_name: str,
    curriculum_history: Optional[List[Dict[str, Any]]] = None
) -> ProblemStatementSchema:
    """Agent 0: Curriculum Director / Problem Formulation Agent with Subsystems & Cumulative Memory."""
    telemetry_summary = build_telemetry_prompt_summary(telemetry)
    
    history_section = ""
    if curriculum_history:
        history_section = "\n--- PRECEDING COURSE MODULES & PREREQUISITES (WHAT STUDENTS ALREADY BUILT) ---\n"
        for item in curriculum_history:
            w = item.get("week")
            t = item.get("title")
            f = item.get("focus", "")
            comps = item.get("components", [])
            comp_str = ", ".join(comps) if comps else "core foundational logic"
            history_section += f"* Week {w}: {t} (Focus: {f}) - Implemented: {comp_str}\n"
        history_section += (
            "DIRECTIVE: Build naturally upon the students' prior knowledge from preceding weeks. "
            "Do not re-teach or duplicate fundamentals built in earlier weeks.\n\n"
        )

    outcomes_str = ""
    if getattr(module, "learning_outcomes", None):
        outcomes_str = f"Target Learning Outcomes for THIS Module:\n" + "\n".join([f"- {o}" for o in module.learning_outcomes]) + "\n\n"

    prompt = (
        f"You are an expert AI & Computing Curriculum Director.\n"
        f"Formulate a domain-grounded coding problem statement and milestone contract for module '{module.title}' (Week {module.week}).\n"
        f"Directives: {module.context}\n"
        f"Difficulty: {module.difficulty}\n\n"
        f"{outcomes_str}"
        f"{history_section}"
        f"{telemetry_summary}\n\n"
        f"FORMULATION DIRECTIVES:\n"
        f"1. DECONSTRUCT SPECIFIC MODULE LEARNING OUTCOMES:\n"
        f"   - Break THIS specific module's declared `Target Learning Outcomes` and `Directives` into 3 progressive milestone subsystems (`milestone_subsystems`).\n"
        f"   - Each milestone must define multiple cooperating components (`ComponentSpec`) with exact Python function/class signatures and type hints.\n"
        f"2. CRITICAL PEDAGOGICAL BOUNDARY (ANTI-BIAS GUARDRAIL):\n"
        f"   - Tailor the subsystems strictly to what THIS specific module is teaching. Do NOT jump ahead or default to training neural networks / CNNs unless this module's learning outcomes explicitly demand deep learning / neural network modeling.\n"
        f"   - For exploratory or data analysis modules: Focus on data ingestion, dataset statistics, image property analysis (resolutions, RGB histograms, contrast, asymmetry), and exploratory reporting. DO NOT train a model or CNN.\n"
        f"   - For feature engineering modules: Focus on extracting quantitative feature vectors (e.g. texture, color moments) and transparent classical baselines.\n"
        f"   - For deep learning modules: Focus on tensor batching, neural architectures, and optimization loops.\n"
        f"   - For explainability modules: Focus on feature attribution, hooks, and error diagnosis.\n"
        f"   - For deployment modules: Focus on inference pipelines and interactive UI interfaces.\n"
        f"3. AUTHENTIC ASSET UTILIZATION:\n"
        f"   - If authentic image assets or results CSV are available (see telemetry above), incorporate them naturally into the exercise instructions and data loading contracts (using relative paths `../../../images/dataset_sample` or `../../../results.csv`).\n"
        f"4. OVERARCHING WORKFLOW:\n"
        f"   - Specify `pipeline_orchestrator_signature`: (e.g. `def run_pipeline(...) -> dict:`) that wires Milestones 1, 2, and 3 together into an overarching workflow.\n"
        f"5. COMPREHENSIVE OVERVIEW DOCUMENT:\n"
        f"   - Write a comprehensive `markdown_overview` document formatted in Github-flavored Markdown explaining: (1) Theoretical concepts for this module, (2) Grounding in domain dataset telemetry, and (3) What students build in each of the 3 milestone subsystems.\n"
    )

    result: ProblemStatementSchema = client.chat.completions.create(
        model=model_name,
        response_model=ProblemStatementSchema,
        max_retries=3,
        max_tokens=8192,
        messages=[
            {"role": "system", "content": "You are an expert AI & Computing Curriculum Director."},
            {"role": "user", "content": prompt}
        ]
    )
    return result
