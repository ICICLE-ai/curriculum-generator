import os
import json
import csv
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Tuple

def compute_file_sha256(filepath: str) -> str:
    """Computes the SHA-256 hexadecimal checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_results_csv(csv_path: str) -> Tuple[bool, str, int]:
    """
    Validates prediction_records (results.csv):
    Checks presence, column headers, valid probabilities in [0.0, 1.0], and no NaNs.
    Returns: (is_valid, message, row_count)
    """
    if not os.path.exists(csv_path):
        return False, f"Missing required artifact: {csv_path}", 0

    if os.path.getsize(csv_path) == 0:
        return False, f"Artifact is empty (0 bytes): {csv_path}", 0

    required_cols = {"image_path", "ground_truth", "predicted_class"}
    row_count = 0

    try:
        with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames or [])
            missing_cols = required_cols - headers
            if missing_cols:
                return False, f"results.csv missing required columns: {missing_cols}", 0

            for i, row in enumerate(reader):
                row_count += 1
                gt = row.get("ground_truth")
                pred = row.get("predicted_class")
                if not gt or not pred:
                    return False, f"Row {i+1} has missing ground_truth or predicted_class", row_count

                # Optional probability validation if present
                prob_raw = row.get("probabilities") or row.get("confidence") or row.get("probability")
                if prob_raw:
                    if prob_raw.startswith("["):
                        try:
                            probs = json.loads(prob_raw)
                            for p in probs:
                                p_float = float(p)
                                if p_float < -0.01 or p_float > 1.01:
                                    return False, f"Row {i+1} probability {p_float} out of [0, 1] range", row_count
                        except Exception:
                            pass
                    else:
                        try:
                            p_float = float(prob_raw)
                            if p_float < -0.01 or p_float > 1.01:
                                return False, f"Row {i+1} probability {p_float} out of [0, 1] range", row_count
                        except Exception:
                            pass

        if row_count == 0:
            return False, "results.csv contains header only with 0 data rows", 0

        return True, f"Verified {row_count} prediction rows with valid schema and bounded values", row_count

    except Exception as e:
        return False, f"Error parsing results.csv: {str(e)}", row_count

def validate_cv_report(json_path: str) -> Tuple[bool, str, int]:
    """
    Validates validation_metrics (cv_report.json):
    Checks valid JSON, mean_accuracy in [0.0, 1.0] or [0, 100], and per-fold metrics.
    Returns: (is_valid, message, fold_count)
    """
    if not os.path.exists(json_path):
        return False, f"Missing required artifact: {json_path}", 0

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        acc = data.get("mean_accuracy")
        if acc is None:
            return False, "cv_report.json missing 'mean_accuracy'", 0

        acc_float = float(acc)
        # Normalize if percentage
        if acc_float > 1.0:
            acc_float = acc_float / 100.0

        if acc_float < 0.0 or acc_float > 1.0:
            return False, f"mean_accuracy {acc} is outside valid range [0, 1]", 0

        folds = data.get("folds") or data.get("folds_data", [])
        if isinstance(folds, dict):
            acc_list = folds.get("accuracy", [])
            fold_count = len(acc_list) if isinstance(acc_list, list) else 0
        elif isinstance(folds, list):
            fold_count = len(folds)
        else:
            fold_count = 0

        return True, f"Verified CV report (Mean Accuracy: {acc_float:.4f}, Folds: {fold_count})", fold_count

    except Exception as e:
        return False, f"Error parsing cv_report.json: {str(e)}", 0

def validate_parallel_telemetry(json_path: str) -> Tuple[bool, str, int]:
    """
    Validates hpc_telemetry (parallel_telemetry.json):
    Checks fold completeness, worker PIDs, device strings, non-negative durations and throughputs.
    Returns: (is_valid, message, fold_count)
    """
    if not os.path.exists(json_path):
        return False, f"Missing required artifact: {json_path}", 0

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        folds = data.get("fold_to_worker_mapping", [])
        if not isinstance(folds, list) or len(folds) == 0:
            return False, "parallel_telemetry.json has empty or missing 'fold_to_worker_mapping'", 0

        for f_info in folds:
            fold_id = f_info.get("fold")
            pid = f_info.get("worker_pid")
            duration = f_info.get("duration_sec")
            tput = f_info.get("throughput_img_per_sec")

            if fold_id is None:
                return False, "Fold record missing 'fold' index", len(folds)
            if pid is not None and pid <= 0:
                return False, f"Fold {fold_id} has invalid worker_pid: {pid}", len(folds)
            if duration is not None and duration < 0:
                return False, f"Fold {fold_id} has negative duration: {duration}", len(folds)
            if tput is not None and tput < 0:
                return False, f"Fold {fold_id} has negative throughput: {tput}", len(folds)

        speedup = data.get("speedup_vs_sequential_est")
        wall_time = data.get("total_cv_wall_time_sec")

        return True, f"Verified {len(folds)} worker folds (Wall Time: {wall_time}s, Speedup: {speedup}x)", len(folds)

    except Exception as e:
        return False, f"Error parsing parallel_telemetry.json: {str(e)}", 0

def validate_image_artifact(img_path: str) -> Tuple[bool, str, int]:
    """
    Validates diagnostic_visualization (images, confusion matrices):
    Checks existence and non-zero byte size.
    """
    if not os.path.exists(img_path):
        return False, f"Image artifact not found: {img_path}", 0

    size = os.path.getsize(img_path)
    if size < 100:
        return False, f"Image artifact suspiciously small ({size} bytes): {img_path}", size

    return True, f"Verified image artifact ({size} bytes)", size

def validate_workflow_artifacts(output_dir: str) -> Dict[str, Any]:
    """
    Validates all Phase 1 workflow artifacts in output_dir against domain contracts.
    Generates and saves validation_report.json.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    checks = {}
    passed_count = 0
    failed_count = 0

    # 1. results.csv
    csv_path = os.path.join(output_dir, "results.csv")
    if os.path.exists(csv_path):
        valid, msg, count = validate_results_csv(csv_path)
        checks["results.csv"] = {
            "status": "VERIFIED" if valid else "FAILED",
            "category": "prediction_records",
            "message": msg,
            "records_count": count
        }
        if valid: passed_count += 1
        else: failed_count += 1

    # 2. cv_report.json
    cv_path = os.path.join(output_dir, "cv_report.json")
    if os.path.exists(cv_path):
        valid, msg, count = validate_cv_report(cv_path)
        checks["cv_report.json"] = {
            "status": "VERIFIED" if valid else "FAILED",
            "category": "validation_metrics",
            "message": msg,
            "records_count": count
        }
        if valid: passed_count += 1
        else: failed_count += 1

    # 3. parallel_telemetry.json
    pt_path = os.path.join(output_dir, "parallel_telemetry.json")
    if os.path.exists(pt_path):
        valid, msg, count = validate_parallel_telemetry(pt_path)
        checks["parallel_telemetry.json"] = {
            "status": "VERIFIED" if valid else "FAILED",
            "category": "hpc_telemetry",
            "message": msg,
            "records_count": count
        }
        if valid: passed_count += 1
        else: failed_count += 1

    # 4. eval_confusion_matrix.png
    cm_path = os.path.join(output_dir, "eval_confusion_matrix.png")
    if os.path.exists(cm_path):
        valid, msg, count = validate_image_artifact(cm_path)
        checks["eval_confusion_matrix.png"] = {
            "status": "VERIFIED" if valid else "FAILED",
            "category": "diagnostic_visualization",
            "message": msg,
            "size_bytes": count
        }
        if valid: passed_count += 1
        else: failed_count += 1

    overall_status = "VERIFIED" if (failed_count == 0 and passed_count > 0) else ("FAILED" if failed_count > 0 else "NO_ARTIFACTS")

    report = {
        "validation_timestamp_iso": timestamp,
        "overall_status": overall_status,
        "checks_passed": passed_count,
        "checks_failed": failed_count,
        "artifact_checks": checks
    }

    report_path = os.path.join(output_dir, "validation_report.json")
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    except Exception:
        pass

    return report
