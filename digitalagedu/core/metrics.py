import os
import time
import json
import csv
from collections import defaultdict
from sklearn.metrics import confusion_matrix
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
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        metrics_per_class[cls] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4)
        }

    # Runtime
    runtime_seconds = round(time.time() - start_time, 2)

    # Summary
    run_summary = {
        "config_file" : os.path.basename(config_path),
        "seed": seed,
        "total_runtime_hours" : round(runtime_seconds/3600, 2),
        "stage_runtime_hours": stage_runtime_hours,
        "total_rows_processed" : total_rows,
        "overall_accuracy_percent": round(accuracy, 2),
        "class_balance": dict(class_balance),
        "error_counts" : dict(error_counts),
        "metrics_per_class": metrics_per_class
    }

    summary_path = os.path.join(output_dir, "run_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(run_summary, f, indent=4)
        print(f"\nRun summary saved to: {summary_path}")

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
