import os
import time
import json
import csv
from collections import defaultdict
from sklearn.metrics import confusion_matrix, roc_auc_score
import matplotlib.pyplot as plt
import seaborn as sns


def generate_run_report(all_results, start_time, config_path, output_dir, seed, stage_runtime_hours):
    """
    Calculates final metrics and saves run_summary.json and results.csv
    """
    total_rows = len(all_results)

    correct_predictions = sum(1 for r in all_results if r.get("predicted_class") == r.get("ground_truth"))
    accuracy = (correct_predictions / total_rows) * 100 if total_rows > 0 else 0



    # Class Balance
    class_balance = defaultdict(int)
    for r in all_results:   
        class_balance[r.get("ground_truth")] += 1

    all_truth = []
    all_preds = []

    # Count errors and calculate metrics
    error_counts = defaultdict(int)
    true_positives = defaultdict(int)
    false_positives = defaultdict(int)
    false_negatives = defaultdict(int)

    for r in all_results:
        truth = r.get("ground_truth")
        pred = r.get("predicted_class")

        all_truth.append(truth)
        all_preds.append(pred)
        
        if truth == pred:
            true_positives[truth] += 1
        else:
            error_counts[f"{truth}_predicted_as_{pred}"] += 1
            false_positives[pred] += 1
            false_negatives[truth] += 1

    # Calculate Precision, Recall, F1 for each class
    metrics_per_class = {}
    for cls in class_balance.keys():
        tp = true_positives[cls]
        fp = false_positives[cls]
        fn = false_negatives[cls]

        tn = total_rows - (tp + fp + fn)
        
        

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        fnr = 1 - recall
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        metrics_per_class[cls] = {
            "precision": round(precision, 4),
            "sensitivity_recall": round(recall, 4),
            "specificity" : round(specificity, 4),
            "false_negative_rate" : round(fnr, 4),
            "false_positive_rate" : round(1 - specificity, 4),
            "f1_score": round(f1, 4)
        }

    # Runtime
    runtime_seconds = round(time.time() - start_time, 2)

    # Get probs for AUC-ROC
    all_probs = []
    has_probs = True
    
    for r in all_results:
        if "probabilities" in r:
            all_probs.append(r["probabilities"])
        else:
            has_probs = False
            break

    auc_roc = None
    if has_probs and len(all_probs) > 0:
        labels = sorted(list(class_balance.keys()))

        if len(labels) == 2:
            # BInary classification
            pos_probs = [p[1] for p in all_probs]
            auc_roc = roc_auc_score(all_truth, pos_probs)

        else:
            # OvR classification
            auc_roc = roc_auc_score(all_truth, all_probs, multi_class="ovr", labels=labels)
    

    # Summary
    run_summary = {
        "config_file" : os.path.basename(config_path),
        "seed": seed,
        "total_runtime_hours" : round(runtime_seconds/3600, 2),
        "stage_runtime_hours": stage_runtime_hours,
        "total_rows_processed" : total_rows,
        "overall_accuracy_percent": round(accuracy, 2),
        "auc_roc": round(auc_roc, 4) if auc_roc else None,
        "class_balance": dict(class_balance),
        "error_counts" : dict(error_counts),
        "metrics_per_class": metrics_per_class,
        "provenance_file": "provenance.json"
    }

    summary_path = os.path.join(output_dir, "run_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(run_summary, f, indent=4)
        print(f"\nRun summary saved to: {summary_path}")

    # Generate and export formal workflow provenance record
    generate_provenance_record(
        config_path=config_path,
        output_dir=output_dir,
        seed=seed,
        total_images=total_rows,
        classes=sorted(list(class_balance.keys()))
    )

    # Generate confusion matrix for evaluation
    labels = sorted(list(class_balance.keys()))
    cm = confusion_matrix(all_truth, all_preds, labels=labels)

    plt.figure(figsize=(10,10))
    sns.heatmap(cm, annot=True, fmt='d',cmap="Blues", xticklabels=labels,yticklabels=labels)
    plt.xlabel('Predicted Class')
    plt.ylabel('Actual Class')
    plt.title("Final Evaluation Confusion Matrix")

    # Save the matrix
    cm_path = os.path.join(output_dir, "eval_confusion_matrix.png")
    plt.savefig(cm_path, bbox_inches='tight')
    plt.close()
    print(f"Evaluation Confusion Matrix saved to {cm_path}")
    

    # Extract every key in order
    fieldnames = []
    for res in all_results:
        for key in res.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    # Write to the csv
    results_file = os.path.join(output_dir, "results.csv")
    with open(results_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(all_results)


def generate_provenance_record(
    config_path: str,
    output_dir: str,
    seed: int = None,
    total_images: int = 0,
    classes: list = None,
    model_backbone: str = "vit_base_patch14_dinov2"
) -> dict:
    """
    Constructs and exports a formal provenance record (provenance.json)
    linking research workflow metadata, execution environment, and datasets.
    """
    import sys
    import platform
    from datetime import datetime

    gpu_info = []
    torch_version = "N/A"
    cuda_version = None
    cuda_available = False

    try:
        import torch
        torch_version = torch.__version__
        cuda_version = torch.version.cuda if torch.cuda.is_available() else None
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            for i in range(torch.cuda.device_count()):
                try:
                    gpu_info.append({
                        "device_id": i,
                        "name": torch.cuda.get_device_name(i),
                        "total_memory_mb": round(torch.cuda.get_device_properties(i).total_memory / (1024 ** 2), 2)
                    })
                except Exception:
                    pass
    except ImportError:
        pass

    provenance_data = {
        "provenance_version": "1.0",
        "timestamp_iso": datetime.utcnow().isoformat() + "Z",
        "run_id": f"run_{seed or int(datetime.utcnow().timestamp())}",
        "seed": seed,
        "config_file": os.path.basename(config_path),
        "dataset_metadata": {
            "total_images_processed": total_images,
            "classes": classes or [],
            "num_classes": len(classes) if classes else 0
        },
        "model_architecture": {
            "backbone": model_backbone,
            "framework": "PyTorch / timm",
            "pretrained_weights": "lvd142m"
        },
        "hardware_environment": {
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
            "cuda_available": cuda_available,
            "gpu_count": len(gpu_info),
            "gpus": gpu_info
        },
        "software_environment": {
            "python_version": sys.version.split()[0],
            "torch_version": torch_version,
            "cuda_version": cuda_version
        }
    }

    prov_path = os.path.join(output_dir, "provenance.json")
    with open(prov_path, "w", encoding="utf-8") as f:
        json.dump(provenance_data, f, indent=4)
    print(f"Workflow provenance record saved to: {prov_path}")
    return provenance_data

