"""
Curated Atomic Visual Recipes (Micro-Patterns) for Presentation Generation.
These modular code snippets are indexed into the ICICLE Qdrant Vector Cloud
(chunk_type="presentation_recipe") and retrieved dynamically by PresentationDesigner
to ground REPL code synthesis in verified slide_kit and visual_kit patterns without
restricting narrative structure or slide deck layout creativity.
"""

from typing import List, Dict, Any

VISUAL_RECIPES: List[Dict[str, Any]] = [
    {
        "id": "recipe_flowchart_pipeline",
        "title": "Pipeline Architecture Flowchart",
        "primary_topic": "pipeline_architecture",
        "topics": ["flowchart", "pipeline", "architecture", "data_flow", "stages"],
        "chunk_type": "presentation_recipe",
        "description": "How to generate a professional dark-themed horizontal workflow diagram connecting data stages with arrows.",
        "text": """### Recipe: Pipeline Architecture Flowchart
```python
# Create horizontal flowchart showing system data pipeline
stages = [
    {"title": "Input Telemetry", "desc": "Raw sensor batches & normalization"},
    {"title": "Feature Extractor", "desc": "Spatial convolution & pooling"},
    {"title": "Classifier Head", "desc": "Softmax distribution & thresholding"},
    {"title": "Evaluation", "desc": "Metric logging & validation report"}
]
flow_img = visual_kit.draw_flowchart(stages=stages, title="End-to-End Pipeline Flow")

# Add to slide with split layout
slide = slide_kit.add_split_slide(
    prs=prs,
    title="System Architecture & Processing Pipeline",
    left_content=["Raw data ingestion", "Automated feature engineering", "Downstream inference"],
    image_path=flow_img
)
```"""
    },
    {
        "id": "recipe_neural_architecture",
        "title": "Deep Neural Network Layer Hierarchy",
        "primary_topic": "model_architecture",
        "topics": ["architecture", "neural_network", "cnn", "layers", "dimensions"],
        "chunk_type": "presentation_recipe",
        "description": "How to draw a layered neural network diagram showing tensor shapes and dimensional transformations.",
        "text": """### Recipe: Neural Network Architecture Diagram
```python
# Diagram depicting layer progression with tensor dimensions
layers = [
    {"name": "Input", "shape": "(3, 224, 224)", "color": visual_kit.Colors.CYAN},
    {"name": "ConvBlock 1", "shape": "(64, 112, 112)", "color": visual_kit.Colors.INDIGO},
    {"name": "ConvBlock 2", "shape": "(128, 56, 56)", "color": visual_kit.Colors.PURPLE},
    {"name": "GlobalPool", "shape": "(128, 1, 1)", "color": visual_kit.Colors.EMERALD},
    {"name": "Linear Head", "shape": "(num_classes)", "color": visual_kit.Colors.ROSE}
]
arch_img = visual_kit.draw_architecture(layers=layers, title="Layer Dimensions & Flow")
slide = slide_kit.add_hero_graphic(prs, title="Model Architecture Breakdown", image_path=arch_img)
```"""
    },
    {
        "id": "recipe_confusion_matrix",
        "title": "Confusion Matrix with Percentages",
        "primary_topic": "evaluation_metrics",
        "topics": ["confusion_matrix", "evaluation", "metrics", "classification", "diagnostics"],
        "chunk_type": "presentation_recipe",
        "description": "How to plot a normalized dark-mode confusion matrix using visual_kit and embed it in a slide.",
        "text": """### Recipe: Confusion Matrix with Counts & Normalization
```python
# Build a confusion matrix over the classes involved in the most frequent real errors.
# error_counts keys look like "<true>_predicted_as_<pred>"; recall is in metrics_per_class.
rs = telemetry["run_summary"]
pairs = sorted(rs["error_counts"].items(), key=lambda kv: -kv[1])[:6]
labels = sorted({c for k, _ in pairs for c in k.split("_predicted_as_")})
idx = {c: i for i, c in enumerate(labels)}
matrix_data = [[0] * len(labels) for _ in labels]
for k, n in rs["error_counts"].items():
    t, p = k.split("_predicted_as_")
    if t in idx and p in idx:
        matrix_data[idx[t]][idx[p]] += n
for c in labels:
    matrix_data[idx[c]][idx[c]] = round(rs["class_balance"][c] * rs["metrics_per_class"][c]["sensitivity_recall"])

cm_img = visual_kit.draw_confusion_matrix(
    matrix=matrix_data,
    labels=labels,
    normalize=True,
    title="Validation Confusion Matrix"
)
slide = slide_kit.add_split_slide(
    prs=prs,
    title="Diagnostic Error Analysis",
    left_content=[
        "High true positive rate indicates robust sensitivity",
        "Low false positive rate limits erroneous triggers",
        "Diagonal dominance demonstrates model calibration"
    ],
    image_path=cm_img
)
```"""
    },
    {
        "id": "recipe_metric_comparison",
        "title": "Comparative Model Benchmark Chart",
        "primary_topic": "evaluation_metrics",
        "topics": ["benchmark", "comparison", "metrics", "baseline", "accuracy"],
        "chunk_type": "presentation_recipe",
        "description": "How to create a multi-bar chart comparing baseline versus custom model metrics.",
        "text": """### Recipe: Multi-Metric Benchmark Comparison
```python
# Compare precision vs recall for the 5 weakest classes (lowest real F1) from this run
mpc = telemetry["run_summary"]["metrics_per_class"]
weakest = sorted(mpc, key=lambda c: mpc[c]["f1_score"])[:5]

bench_img = visual_kit.draw_metric_comparison(
    categories=weakest,
    series_a=[mpc[c]["precision"] for c in weakest],
    series_b=[mpc[c]["sensitivity_recall"] for c in weakest],
    label_a="Precision",
    label_b="Recall",
    title="Weakest Classes: Precision vs Recall"
)
slide = slide_kit.add_hero_graphic(prs, title="Where the Model Struggles", image_path=bench_img)
```"""
    },
    {
        "id": "recipe_class_distribution",
        "title": "Class Distribution Donut Chart",
        "primary_topic": "exploratory_data_analysis",
        "topics": ["distribution", "eda", "classes", "imbalance", "dataset"],
        "chunk_type": "presentation_recipe",
        "description": "How to generate a donut or bar distribution chart visualizing dataset class balance.",
        "text": """### Recipe: Class Distribution Chart
```python
# Visualize dataset class balance with donut or bar chart
class_counts = telemetry["run_summary"]["class_balance"]
labels = list(class_counts.keys())
values = list(class_counts.values())

dist_img = visual_kit.draw_distribution(
    labels=labels,
    values=values,
    chart_type="donut",
    title="Dataset Class Balance"
)
slide = slide_kit.add_split_slide(
    prs=prs,
    title="Dataset Demographics & Balance",
    left_content=[
        f"Total evaluated samples: {sum(values)}",
        "Monitored class balance to prevent majority-class bias",
        "Stratified partitioning applied during training"
    ],
    image_path=dist_img
)
```"""
    },
    {
        "id": "recipe_metric_kpi_badges",
        "title": "KPI Metric Cards Slide",
        "primary_topic": "evaluation_metrics",
        "topics": ["metrics", "kpi", "cards", "summary", "badges"],
        "chunk_type": "presentation_recipe",
        "description": "How to generate a high-impact slide with 3 side-by-side KPI cards displaying performance figures and deltas.",
        "text": """### Recipe: KPI Metric Badges Slide
```python
# Render 3 prominent KPI summary cards from this run's real metrics
rs = telemetry["run_summary"]
mpc = rs["metrics_per_class"]
macro_f1 = 100 * sum(m["f1_score"] for m in mpc.values()) / len(mpc)
worst = min(mpc, key=lambda c: mpc[c]["f1_score"])

slide = slide_kit.add_metric_slide(
    prs=prs,
    title="System Performance Highlights",
    metrics=[
        {"label": "Test Accuracy", "value": f"{rs['overall_accuracy_percent']:.1f}%", "delta": f"{rs['total_rows_processed']} samples"},
        {"label": "Macro F1-Score", "value": f"{macro_f1:.1f}%", "delta": f"AUC-ROC {rs['auc_roc']:.3f}"},
        {"label": "Weakest Class F1", "value": f"{100 * mpc[worst]['f1_score']:.1f}%", "delta": worst}
    ]
)
```"""
    },
    {
        "id": "recipe_subsystem_cards",
        "title": "Three-Column Subsystem Architecture Cards",
        "primary_topic": "system_design",
        "topics": ["cards", "subsystems", "components", "design", "modular"],
        "chunk_type": "presentation_recipe",
        "description": "How to present 3 modular subsystems with distinct icons, titles, and technical bullet descriptions.",
        "text": """### Recipe: Subsystem Component Cards
```python
# Present 3 engineering subsystems side-by-side
slide = slide_kit.add_card_slide(
    prs=prs,
    title="Subsystem Implementation & Milestones",
    cards=[
        {
            "title": "1. Dataset Ingestion",
            "bullets": ["Dynamic image loader with fallback", "Randomized augmentation pipeline", "Stratified batch tensor creation"]
        },
        {
            "title": "2. Neural Backbone",
            "bullets": ["Parameterized convolutional blocks", "Batch normalization & residual skips", "Adaptive average pooling layer"]
        },
        {
            "title": "3. Optimization & Testing",
            "bullets": ["AdamW with cosine annealing", "Cross-entropy loss with label smoothing", "Automated contract unit test harness"]
        }
    ]
)
```"""
    },
    {
        "id": "recipe_code_architecture_slide",
        "title": "Code Implementation Architecture Slide",
        "primary_topic": "code_implementation",
        "topics": ["code", "implementation", "syntax", "solution", "scaffolding"],
        "chunk_type": "presentation_recipe",
        "description": "How to present core Python classes and method signatures using dark syntax highlighting.",
        "text": """### Recipe: Code Architecture Slide
```python
# Format key component method signatures for student review
code_snippet = \"\"\"class ModelPipeline(nn.Module):
    def __init__(self, in_channels: int, num_classes: int):
        super().__init__()
        self.backbone = ConvolutionalBackbone(in_channels)
        self.classifier = LinearClassifier(num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.backbone(x)
        return self.classifier(features)\"\"\"

slide = slide_kit.add_code_slide(
    prs=prs,
    title="Core Pipeline Interface & Signatures",
    code=code_snippet,
    notes="The forward method connects the feature backbone directly to the projection classifier."
)
```"""
    },
    {
        "id": "recipe_loss_training_curve",
        "title": "Loss & Convergence Dynamics Plot",
        "primary_topic": "model_training",
        "topics": ["loss", "convergence", "training", "epochs", "curve", "matplotlib"],
        "chunk_type": "presentation_recipe",
        "description": "How to plot stylized training and validation loss curves with overfitting threshold lines.",
        "text": """### Recipe: Training Loss Convergence Curve
```python
# Plot training vs validation loss over epochs using Matplotlib with dark theme
fig, ax = visual_kit.create_figure(title="Convergence History & Loss Dynamics", xlabel="Epoch", ylabel="Cross-Entropy Loss")
epochs = list(range(1, 16))
train_loss = [1.20, 0.95, 0.72, 0.54, 0.42, 0.33, 0.27, 0.22, 0.18, 0.15, 0.13, 0.11, 0.10, 0.09, 0.08]
val_loss =   [1.25, 1.01, 0.79, 0.62, 0.51, 0.44, 0.39, 0.36, 0.34, 0.33, 0.32, 0.31, 0.31, 0.30, 0.30]

ax.plot(epochs, train_loss, color=visual_kit.Colors.CYAN, lw=2.5, marker="o", markersize=4, label="Training Loss")
ax.plot(epochs, val_loss, color=visual_kit.Colors.ROSE, lw=2.5, marker="s", markersize=4, linestyle="--", label="Validation Loss")
ax.legend(frameon=True, facecolor=visual_kit.Colors.SURFACE_LIGHT, edgecolor=visual_kit.Colors.BORDER)
loss_img = visual_kit.save_figure(fig, filename="training_convergence.png")

slide = slide_kit.add_split_slide(
    prs=prs,
    title="Optimization Dynamics & Stability",
    left_content=[
        "Monotonic loss reduction confirms gradient health",
        "Minimal divergence between train and validation paths",
        "Plateau observed around epoch 12 indicates optimal convergence"
    ],
    image_path=loss_img
)
```"""
    },
    {
        "id": "recipe_roc_auc_curve",
        "title": "ROC Analysis & AUC Score Curve",
        "primary_topic": "evaluation_metrics",
        "topics": ["roc", "auc", "curve", "sensitivity", "specificity", "evaluation"],
        "chunk_type": "presentation_recipe",
        "description": "How to plot a Receiver Operating Characteristic (ROC) curve with shaded AUC area.",
        "text": """### Recipe: ROC Curve with Shaded AUC Area
```python
# Plot ROC curve with shaded area under the curve
fig, ax = visual_kit.create_figure(title="Receiver Operating Characteristic (ROC)", xlabel="False Positive Rate", ylabel="True Positive Rate")
fpr = [0.0, 0.02, 0.05, 0.10, 0.18, 0.25, 0.40, 0.60, 1.0]
tpr = [0.0, 0.45, 0.72, 0.85, 0.92, 0.95, 0.98, 0.99, 1.0]

ax.plot(fpr, tpr, color=visual_kit.Colors.PURPLE, lw=3, label="Classifier (AUC = 0.96)")
ax.plot([0, 1], [0, 1], color=visual_kit.Colors.TEXT_MUTED, linestyle=":", lw=1.5, label="Random Guess (0.50)")
ax.fill_between(fpr, tpr, alpha=0.15, color=visual_kit.Colors.PURPLE)
ax.legend(frameon=True, facecolor=visual_kit.Colors.SURFACE_LIGHT, edgecolor=visual_kit.Colors.BORDER)
roc_img = visual_kit.save_figure(fig, filename="roc_analysis.png")

slide = slide_kit.add_hero_graphic(prs, title="ROC Analysis & Discrimination Capacity", image_path=roc_img)
```"""
    },
    {
        "id": "recipe_animated_surface_loss",
        "title": "3D Loss Landscape Orbit Animation",
        "primary_topic": "model_optimization",
        "topics": ["animation", "3d", "loss_surface", "optimization", "orbit", "video"],
        "chunk_type": "presentation_recipe",
        "description": "How to generate an animated 3D optimization surface and embed it into a slide deck.",
        "text": """### Recipe: 3D Surface Loss Landscape Animation
```python
# Generate a 3D loss surface orbit MP4 animation
anim_path = visual_kit.render_3d_surface_orbit(
    function_type="loss_surface",
    n_frames=30,
    fps=15,
    filename="loss_landscape.mp4"
)

# Embed into slide
slide = slide_kit.add_split_slide(
    prs=prs,
    title="Loss Landscape & Convexity Geometry",
    left_content=[
        "3D topographical visualization of error gradients",
        "Illustrates local minima avoidance via momentum",
        "Smooth descent trajectory achieved with adaptive learning rates"
    ],
    image_path=anim_path
)
```"""
    },
    {
        "id": "recipe_dataset_sample_grid",
        "title": "Multi-Image Inspection Grid",
        "primary_topic": "data_inspection",
        "topics": ["grid", "images", "dataset", "samples", "inspection"],
        "chunk_type": "presentation_recipe",
        "description": "How to arrange multiple sample inspection images with titles in a cohesive slide layout.",
        "text": """### Recipe: Dataset Sample Inspection Grid
```python
# Draw sample visualization grid with matplotlib
fig, axes = plt.subplots(1, 3, figsize=(10, 3.5), facecolor=visual_kit.Colors.SURFACE)
classes = ["Sample A", "Sample B", "Sample C"]
for idx, ax in enumerate(axes):
    synthetic_patch = np.random.rand(64, 64)
    ax.imshow(synthetic_patch, cmap="plasma")
    ax.set_title(classes[idx], color=visual_kit.Colors.TEXT_PRIMARY, fontsize=12)
    ax.axis("off")
grid_img = visual_kit.save_figure(fig, filename="sample_grid.png")

slide = slide_kit.add_hero_graphic(prs, title="Domain Data Sample Inspection", image_path=grid_img)
```"""
    }
]

