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

    return telemetry

def build_telemetry_prompt_summary(telemetry: Dict[str, Any]) -> str:
    """Formats raw Phase 1 telemetry dict into a clean prompt context string for Agent 0."""
    if not telemetry:
        return "No Phase 1 pipeline telemetry available. Use generic PyTorch deep learning context."

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

    return "\n".join(summary_lines)

def formulate_problem_statement(
    module, 
    telemetry: Dict[str, Any], 
    client: instructor.Instructor, 
    model_name: str
) -> ProblemStatementSchema:
    """Agent 0: Curriculum Director / Problem Formulation Agent."""
    telemetry_summary = build_telemetry_prompt_summary(telemetry)
    
    prompt = (
        f"You are an expert AI Curriculum Director and Applied Deep Learning Educator.\n"
        f"Formulate a domain-grounded coding problem statement for module '{module.title}' (Week {module.week}).\n"
        f"Directives: {module.context}\n"
        f"Difficulty: {module.difficulty}\n\n"
        f"{telemetry_summary}\n\n"
        f"FORMULATION DIRECTIVES:\n"
        f"1. Analyze Phase 1 telemetry (error counts, class imbalance, precision/recall per class, and contrastive samples).\n"
        f"2. Formulate a realistic, domain-specific problem statement using the exact target class names and dataset metrics provided in telemetry.\n"
        f"3. Specify clear synthetic tensor input/output shape contracts matching the dataset modality.\n"
        f"4. Focus the exercise on addressing the primary model failure modes and performance gaps discovered in Phase 1.\n"
        f"5. Write a comprehensive `markdown_overview` document formatted in Github-flavored Markdown containing:\n"
        f"   - `# [Module Title] Concept Overview`\n"
        f"   - `## 1. Theoretical Background` (explaining the deep learning concept)\n"
        f"   - `## 2. Domain & Pipeline Telemetry Grounding` (explaining how this concept connects to the Phase 1 dataset & error cases)\n"
        f"   - `## 3. Hands-on Student Exercise & Objectives` (explaining what the student is building, implementing, and solving)\n"
    )

    result: ProblemStatementSchema = client.chat.completions.create(
        model=model_name,
        response_model=ProblemStatementSchema,
        max_retries=3,
        max_tokens=8192,
        messages=[
            {"role": "system", "content": "You are an expert AI Curriculum Director."},
            {"role": "user", "content": prompt}
        ]
    )
    return result
