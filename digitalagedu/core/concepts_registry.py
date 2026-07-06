# =====================================================================
# CONCEPT REGISTRY
# Stores concept mappings, resource references, and detailed lesson guides
# for the 6-Month (24-Week) medical computer vision curriculum.
# =====================================================================

CONCEPT_MAP = {
    "numpy basics": "numpy_basics.py.j2",
    "pandas & matplotlib": "pandas_analytics.py.j2",
    "deep learning foundations": "pytorch_basics.py.j2",
    "interactive image segmentation": "interactive_segmentation.py.j2",
    "pytorch datasets & dataloaders": "image_datasets.py.j2",
    "custom convolutional neural networks": "custom_cnn.py.j2",
    "cnn optimization, regularization & checkpointing": "cnn_optimization.py.j2",
    "transfer learning & backbone benchmarking": "transfer_learning.py.j2",
    "deep learning semantic segmentation & u-net": "semantic_segmentation.py.j2",
    "explainable ai & grad-cam": "explainable_ai.py.j2",
    "image embeddings, clustering & semantic search": "vector_embeddings.py.j2",
    "vision-language models": "vlm_diagnostics.py.j2",
    "capstone integration & gradio deployment": "gradio_deployment.py.j2"
}

RESOURCE_LINKS = {
    "numpy_basics": [
        {"name": "Official NumPy Quickstart Guide", "url": "https://numpy.org/doc/stable/user/quickstart.html", "description": "Hands-on introduction to arrays, shapes, indexing, and vector operations."},
        {"name": "3Blue1Brown: Essence of Linear Algebra", "url": "https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab", "description": "Excellent visual animations explaining vectors, matrix multiplication, and spatial transforms."},
        {"name": "NumPy Illustrated: A Visual Guide", "url": "https://medium.com/swlh/numpy-illustrated-the-visual-guide-to-numpy-3b1d6e8a7615", "description": "Highly visual layouts showing broadcasting, slicing, and matrix dimensions."}
    ],
    "pandas_analytics": [
        {"name": "Official Pandas Comparison to Spreadsheet/SQL", "url": "https://pandas.pydata.org/docs/getting_started/comparison/index.html", "description": "Relatable lookup maps comparing Excel operations directly to Pandas methods."},
        {"name": "Python Graph Gallery (Matplotlib)", "url": "https://python-graph-gallery.com/", "description": "A curated visual reference showing copy-paste code blocks for beautiful line/bar/scatter plots."},
        {"name": "Real Python: Pandas GroupBy Guide", "url": "https://realpython.com/pandas-groupby/", "description": "A comprehensive deep dive into split-apply-combine dataset operations."}
    ],
    "pytorch_basics": [
        {"name": "PyTorch Official Neural Network Tutorial", "url": "https://pytorch.org/tutorials/beginner/blitz/neural_networks_tutorial.html", "description": "Step-by-step introduction to defining model layers, computing loss, and backward propagation."},
        {"name": "3Blue1Brown: Neural Networks Visual Series", "url": "https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi", "description": "Fascinating visual explanations detailing weights, biases, and gradient descent backprop math."},
        {"name": "Playground TensorFlow", "url": "https://playground.tensorflow.org/", "description": "An interactive web portal where you can train neural networks visually in real-time."}
    ],
    "interactive_segmentation": [
        {"name": "OpenCV Mouse Callback Tutorial", "url": "https://docs.opencv.org/4.x/db/d5b/tutorial_py_mouse_handling.html", "description": "Learn to capture mouse click coordinates and draw overlays onto interactive windows."},
        {"name": "Segment Anything Model (SAM) Demo", "url": "https://segment-anything.com/demo", "description": "Meta AI's interactive demo showcasing point-and-click pixel mask segmentation."},
        {"name": "Real Python: Image Processing with OpenCV", "url": "https://realpython.com/image-processing-with-opencv-python/", "description": "Practical guides to handling color spaces, thresholds, and filters in OpenCV."}
    ],
    "image_datasets": [
        {"name": "PyTorch Custom Dataset & Dataloader Docs", "url": "https://pytorch.org/tutorials/beginner/basics/data_tutorial.html", "description": "Official guides explaining dataset subclassing, lazy loading, and batching pipelines."},
        {"name": "PyTorch Disk I/O Performance Tuning", "url": "https://pytorch.org/docs/stable/data.html", "description": "Learn how num_workers, pin_memory, and batch sizes affect training bottlenecks on HPC clusters."},
        {"name": "How to Load Custom Image Datasets in PyTorch", "url": "https://machinelearningmastery.com/loading-custom-image-datasets-for-deep-learning-in-pytorch/", "description": "Visual walkthrough of structuring folders, applying transforms, and parsing class indexes."}
    ],
    "custom_cnn": [
        {"name": "Convolutional Neural Networks (CS231n Stanford Guide)", "url": "https://cs231n.github.io/convolutional-networks/", "description": "Rigorous academic guide explaining spatial dimension changes, receptive fields, and visual features."},
        {"name": "CNN Explainer: Interactive 3D Visualization", "url": "https://poloclub.github.io/cnn-explainer/", "description": "Stunning interactive tool visualizing kernel slides, feature channels, and pooling in real-time."},
        {"name": "PyTorch Conv2d Documentation", "url": "https://pytorch.org/docs/stable/generated/torch.nn.Conv2d.html", "description": "API specifications for padding, strides, dilations, and parameter shapes."}
    ],
    "cnn_optimization": [
        {"name": "BatchNorm and Dropout Visual Explanations", "url": "https://towardsdatascience.com/batch-normalization-and-dropout-in-neural-networks-explained-with-animations-5b3c3fb2b23a", "description": "Animated visual intuition showing how scale stabilization and network thinning prevent overfitting."},
        {"name": "PyTorch Optimizers and Learning Rate Schedulers Docs", "url": "https://pytorch.org/docs/stable/optim.html", "description": "Overview of SGD, Adam, StepLR, and CosineAnnealing scheduling methods."},
        {"name": "PyTorch Model Saving and Loading Best Practices", "url": "https://pytorch.org/tutorials/beginner/saving_loading_models.html", "description": "Detailed guides on state_dicts, checkpoints, resume training, and weight serialization."}
    ],
    "transfer_learning": [
        {"name": "PyTorch Transfer Learning Tutorial", "url": "https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html", "description": "Code patterns showing how to load pretrained backbones and configure feature extractor freezes."},
        {"name": "ResNet Original Research Paper (He et al.)", "url": "https://arxiv.org/abs/1512.03385", "description": "The landmark paper introducing deep residual connections to resolve vanishing gradients."},
        {"name": "DINOv2: Self-supervised Vision Models (Meta AI)", "url": "https://ai.meta.com/blog/dinov2-self-supervised-vision-models/", "description": "Meta AI's blog explaining how self-supervised DINOv2 learns generic, high-performance features."}
    ],
    "semantic_segmentation": [
        {"name": "U-Net Research Paper (Ronneberger et al.)", "url": "https://arxiv.org/abs/1505.04597", "description": "The foundational biomedical semantic segmentation paper introducing skip connections and encoder-decoders."},
        {"name": "Transpose Convolution vs Bilinear Upsampling", "url": "https://distill.pub/2016/deconv-checkerboard/", "description": "An interactive guide explaining deconvolution artifacts and spatial upscaling."},
        {"name": "PyTorch Semantic Segmentation Step-by-Step", "url": "https://pytorch.org/vision/main/models/u2net.html", "description": "Implementing segmentation models, pixel classification, and loss evaluations."}
    ],
    "explainable_ai": [
        {"name": "Grad-CAM Original Research Paper (Selvaraju et al.)", "url": "https://arxiv.org/abs/1610.02391", "description": "Flesh out Grad-CAM mathematical formulations using backpropagation gradients to explain CNN predictions."},
        {"name": "Visualizing CNN Attention Maps", "url": "https://towardsdatascience.com/demystifying-convolutional-neural-networks-with-grad-cam-5f212cf5187e", "description": "Hands-on guide mapping weights of the final conv layers into visible attention heatmaps."},
        {"name": "Captum PyTorch Attribution Library Docs", "url": "https://captum.ai/", "description": "Official documentation for PyTorch's comprehensive explainable AI and model interpretability framework."}
    ],
    "vector_embeddings": [
        {"name": "Vector Search & Cosine Similarity Intuition", "url": "https://www.pinecone.io/learn/vector-similarity/", "description": "Practical guide explaining spatial embeddings, dot product, Euclidean distance, and cosine similarity."},
        {"name": "Scikit-Learn PCA Dimensionality Reduction", "url": "https://scikit-learn.org/stable/modules/decomposition.html#pca", "description": "Mathematical overview of projecting high-dimensional matrices onto primary component axes."},
        {"name": "t-SNE / UMAP Dimensionality Reduction Visual Guide", "url": "https://distill.pub/2016/misread-tsne/", "description": "An interactive visual guide showing how t-SNE projects high-dimensional vector clusters onto 2D grids."}
    ],
    "vlm_diagnostics": [
        {"name": "HuggingFace Phi-3-Vision Integration Guide", "url": "https://huggingface.co/microsoft/Phi-3-vision-128k-instruct", "description": "Guide to loading Phi-3, passing vision embeddings, and generating structured text rationales."},
        {"name": "Overview of Vision-Language Models", "url": "https://huggingface.co/learn/cookbook/fine_tuning_vlm", "description": "Understand multi-modal tokenizers, text-image projection layers, and autoregressive generation."},
        {"name": "Visual Prompt Engineering Best Practices", "url": "https://help.openai.com/en/articles/8480585-gpt-4-system-prompt-writing", "description": "Designing clean text templates to control visual analysis outputs."}
    ],
    "gradio_deployment": [
        {"name": "Gradio Quickstart Guide", "url": "https://gradio.app/quickstart/", "description": "Build interactive web interfaces around your model functions with 5 lines of Python."},
        {"name": "HuggingFace Spaces Deployment Portal", "url": "https://huggingface.co/docs/hub/spaces-sdks-gradio", "description": "Hosting your Gradio web applications on public cloud servers for free."},
        {"name": "Building Interactive AI Web Interfaces in Python", "url": "https://realpython.com/gradio-python/", "description": "Full-stack introduction to building interactive front-ends for machine learning models."}
    ]
}

CONCEPT_GUIDES = {
    "numpy_basics": {
        "core_concepts": [
            {"name": "Multidimensional Arrays (Ndarrays)", "description": "NumPy arrays are grid-like, homogenous blocks of numerical data of the same type. They allow memory-efficient, contiguous storage which is critical for processing images, where pixel values represent high-density spatial metrics."},
            {"name": "Vectorization and Broadcasting", "description": "By eliminating explicit Python loops, vectorization offloads operations directly to compiled C code (SIMD instructions). Broadcasting allows arithmetic operations to run across mismatched shapes (e.g., adding a single bias scalar or a channel-wise vector to an entire 3D image grid) safely and instantly without duplicating memory."}
        ],
        "math_formulas": [
            {
                "name": "Z-Score Matrix Normalization",
                "equation": "Z = \\frac{x - \\mu}{\\sigma}",
                "variables": {"x": "Original pixel coordinate value", "\\mu": "Mean channel pixel value", "\\sigma": "Standard deviation of the channel"},
                "purpose": "Standardizes visual features to a zero-mean and unit variance distribution, accelerating optimization convergence and preventing gradient scaling anomalies in early training stages."
            }
        ],
        "functions": [
            {
                "name": "statistics_and_standardization",
                "description": "Applies Z-score normalization to standardize numerical grid matrices.",
                "real_world": "Prepares medical datasets by smoothing brightness variations and aligning pixel ranges before feeding them to neural layers.",
                "importance": "Standardizes raw data bounds so optimization parameters converge predictably."
            },
            {
                "name": "extract_patches",
                "description": "Slices 2D spatial matrices into localized grid patches using strides.",
                "real_world": "Extracts sub-regions from gigapixel pathology scans (WSI) that exceed GPU memory limits.",
                "importance": "Enables region-of-interest segmentation and training on massive medical dimensions."
            }
        ],
        "pitfalls": [
            {"name": "Out-of-Bounds Slicing", "description": "Slicing indices incorrectly can cause silent data truncation or size anomalies down the pipeline."},
            {"name": "Memory Copy vs. View Confusion", "description": "Modifying a sliced NumPy array modifies the original array because slices are memory views, not deep copies."}
        ]
    },
    "pandas_analytics": {
        "core_concepts": [
            {"name": "Tabular Data Structures", "description": "Pandas DataFrames and Series model relational tabular outputs. In ML, this is used to store prediction histories, loss metrics, training times, and diagnostic statistics."},
            {"name": "Active Learning & Failure Mining", "description": "By grouping and filtering logs, we identify cases where the model made incorrect classifications with high confidence. We feed these 'hard negatives' back into our dataset to refine boundary performance."}
        ],
        "math_formulas": [
            {
                "name": "Classification Accuracy Rate",
                "equation": "Accuracy = \\frac{TP + TN}{TP + TN + FP + FN}",
                "variables": {"TP": "True Positives", "TN": "True Negatives", "FP": "False Positives", "FN": "False Negatives"},
                "purpose": "Provides a global performance metric representing the proportion of correct decisions across all classifications."
            }
        ],
        "functions": [
            {
                "name": "handle_missing_values",
                "description": "Fills missing values (NaNs) in the prediction confidence records using a default or mean value.",
                "real_world": "Cleans incomplete clinical records, preventing pipeline execution halts from null values.",
                "importance": "Ensures downstream models receive clean, fully populated tensors."
            },
            {
                "name": "find_hardest_samples",
                "description": "Filters and sorts predictions to isolate misclassified images with high confidence scores.",
                "real_world": "Automates active learning by flagging the model's most critical blind spots for human doctor re-labeling.",
                "importance": "Targets data collection directly at training weaknesses."
            }
        ],
        "pitfalls": [
            {"name": "SettingWithCopyWarning", "description": "Attempting to assign values directly to slices of a DataFrame causes silent update failures. Always use `.loc` instead."},
            {"name": "Data Leakage", "description": "Using validation/test distributions to impute training NaNs leaks statistics, yielding overly optimistic results."}
        ]
    },
    "pytorch_basics": {
        "core_concepts": [
            {"name": "Multi-Layer Perceptron (MLP)", "description": "A baseline feedforward neural network comprising fully connected (dense) linear layers interspersed with non-linear activations (e.g. ReLU)."},
            {"name": "Backpropagation & Auto-Grad", "description": "Computes the gradients of the loss function with respect to weights via the chain rule, updating parameter states in the opposite direction of the gradient to minimize prediction error."}
        ],
        "math_formulas": [
            {
                "name": "Binary Cross-Entropy (BCE) Loss",
                "equation": "L_{BCE} = -\\frac{1}{N} \\sum_{i=1}^N [y_i \\log(p_i) + (1-y_i) \\log(1-p_i)]",
                "variables": {"y_i": "Binary ground-truth label (0 or 1)", "p_i": "Predicted probability of target class"},
                "purpose": "Measures classification error on probability outputs, heavily penalizing confident wrong answers."
            },
            {
                "name": "L2 Weight Decay Regularization",
                "equation": "L_{total} = L_{BCE} + \\frac{\\lambda}{2} \\sum ||w||^2",
                "variables": {"\\lambda": "Regularization coefficient (weight decay)", "w": "Model weight vectors"},
                "purpose": "Penalizes large weight coefficients, enforcing simpler boundaries and mitigating overfitting."
            }
        ],
        "functions": [
            {
                "name": "train_step_with_l2",
                "description": "Executes a forward pass, manual L2 penalty calculation, backprop, and optimizer step.",
                "real_world": "Underpins model updates in training pipelines, keeping weight values small and generalized.",
                "importance": "Demonstrates backprop steps and weight regularization mechanics."
            }
        ],
        "pitfalls": [
            {"name": "Forgetting to Zero Gradients", "description": "In PyTorch, gradients accumulate. Skipping `optimizer.zero_grad()` mixes steps, causing weight explosions."},
            {"name": "Shape Mismatches during Forward Passes", "description": "Linear layers require exact matrix multiplications. Mismatched hidden dimensions throw compile errors."}
        ]
    },
    "interactive_segmentation": {
        "core_concepts": [
            {"name": "Classical Image Segmentation", "description": "Grouping pixels into regions of interest based on color, edge density, or seed similarity without heavy deep networks."},
            {"name": "OpenCV Interactive Event Listening", "description": "Connecting user actions (mouse clicks) to processing triggers, allowing real-time segmentation tuning."}
        ],
        "math_formulas": [
            {
                "name": "Spatial Image Moments & Centroids",
                "equation": "M_{ij} = \\sum_{x,y} x^i y^j I(x,y), \\quad cX = \\frac{M_{10}}{M_{00}}, \\quad cY = \\frac{M_{01}}{M_{00}}",
                "variables": {"I(x,y)": "Binary pixel intensity at coordinate (x,y)", "M_{00}": "Total mass (area) of mask", "cX, cY": "Centroid coordinates"},
                "purpose": "Calculates the geometric center of mass of a visual mask to track lesion centers over time."
            }
        ],
        "functions": [
            {
                "name": "calculate_mask_centroid",
                "description": "Extracts spatial moments using `cv2.moments` to compute coordinates.",
                "real_world": "Tracks growth or coordinates of skin boundaries over sequential medical visits.",
                "importance": "Underpins target alignment and tracking metrics."
            }
        ],
        "pitfalls": [
            {"name": "Coordinate Axis Swapping", "description": "OpenCV coordinates use (X, Y) whereas NumPy array shapes use (Row/Height, Col/Width). Swapping them causes index crashes."},
            {"name": "Moments Division By Zero", "description": "Dividing by $M_{00}$ on empty masks throws execution errors. A safety branch is required."}
        ]
    },
    "image_datasets": {
        "core_concepts": [
            {"name": "Custom Datasets subclassing", "description": "Creating custom data interfaces that lazy-load single samples from directories, preventing GPU memory exhaustion."},
            {"name": "Dataloader Batching & Threading", "description": "Orchestrates multi-processing queues, prefetching, and shuffling batches to feed the GPU training loop continuously."}
        ],
        "math_formulas": [
            {
                "name": "Dataset-Wide Channel Mean",
                "equation": "\\mu_c = \\frac{1}{N \\cdot H \\cdot W} \\sum_{i, y, x} I_c(i, y, x)",
                "variables": {"I_c": "Pixel channel value", "N": "Total sample size count", "H, W": "Height and width dimensions"},
                "purpose": "Calculates reference statistics across all pixels to apply normalization transforms before training."
            }
        ],
        "functions": [
            {
                "name": "calculate_dataset_stats",
                "description": "Iterates over the dataset to calculate mean and standard deviation across channels.",
                "real_world": "Computes dataset-specific normalizations for unique medical images (e.g. grayscale X-rays vs RGB skin scans).",
                "importance": "Eliminates visual bias from unique scanner lighting ranges."
            }
        ],
        "pitfalls": [
            {"name": "Blocking Lazy-Loading Disk I/O", "description": "Performing expensive transformations (like disk resizing) inside `__getitem__` stalls the pipeline. Always pre-process or optimize raw files."},
            {"name": "Shuffling Validation Sets", "description": "Shuffling validation or test sets is useless, wastes compute, and ruins index comparisons."}
        ]
    },
    "custom_cnn": {
        "core_concepts": [
            {"name": "Convolutional Operations", "description": "Applying small sliding spatial filters (kernels) over feature matrices to capture edges, textures, and shapes while preserving spatial locality."},
            {"name": "Downsampling (Pooling)", "description": "Reduces resolution while preserving core features, extending receptive fields and lowering overall parameter sizes."}
        ],
        "math_formulas": [
            {
                "name": "Output Dimension Shape Logic",
                "equation": "O = \\lfloor \\frac{I - K + 2P}{S} \\rfloor + 1",
                "variables": {"I": "Input dimension size", "K": "Kernel size", "P": "Padding size", "S": "Stride size"},
                "purpose": "Traces how image spatial resolutions contract across successive network layers."
            },
            {
                "name": "Conv Layer Parameters Count",
                "equation": "Parameters = C_{out} \\cdot (C_{in} \\cdot K^2 + 1)",
                "variables": {"C_{in}": "Input channel count", "C_{out}": "Output channel count", "K": "Kernel size"},
                "purpose": "Calculates exactly how many weight values are trained in a single convolutional operation."
            }
        ],
        "functions": [
            {
                "name": "cnn_block_analysis",
                "description": "Calculates dimension changes, parameters, and memory bytes for a CNN block.",
                "real_world": "Estimates hardware parameters and GPU footprint constraint envelopes for mobile or edge deployment.",
                "importance": "Validates network viability on hardware targets before starting expensive builds."
            }
        ],
        "pitfalls": [
            {"name": "Flatten Dims Over-reduction", "description": "Over-pooling input matrices down to zero throws parameter shape exceptions during fully connected flatten stages."},
            {"name": "Incorrect Padding Configuration", "description": "Forgetting padding causes spatial dimensions to shrink rapidly, discarding boundary features in early layers."}
        ]
    },
    "cnn_optimization": {
        "core_concepts": [
            {"name": "Batch Normalization (BatchNorm)", "description": "Normalizes layer inputs per batch during training. This stabilizes activations, mitigates internal covariate shift, and allows higher learning rates."},
            {"name": "Dropout Regularization", "description": "Randomly deactivates neurons during training. This forces the network to learn redundant representations, preventing reliance on spurious correlations."}
        ],
        "math_formulas": [
            {
                "name": "Step Learning Rate Decay",
                "equation": "\\eta_t = \\eta_0 \\cdot \\gamma^{\\lfloor t / s \\rfloor}",
                "variables": {"\\eta_t": "Learning rate at epoch t", "\\eta_0": "Initial learning rate", "\\gamma": "Decay factor (e.g. 0.1)", "s": "Step size decay interval"},
                "purpose": "Decays optimization step sizes over time, helping the model settle into local minima."
            }
        ],
        "functions": [
            {
                "name": "audit_checkpoint_integrity",
                "description": "Scans state dict weights, LRs, and classes in checkpoint files prior to loading.",
                "real_world": "Guarantees training restarts reliably on HPC nodes without failing due to silent weight mismatch bugs.",
                "importance": "Prevents hours of corrupted, unstable optimization runs."
            }
        ],
        "pitfalls": [
            {"name": "Eval Mode Swapping Skip", "description": "Failing to switch to `model.eval()` before validation leaves Dropout active and BatchNorm updating, ruining inference predictions."},
            {"name": "Partial State Restores", "description": "Loading checkpoints with layers that have different shapes silently bypasses updates, leaving target weights untrained."}
        ]
    },
    "transfer_learning": {
        "core_concepts": [
            {"name": "Pretrained Backbone Benchmarking", "description": "Using deep networks (like ResNet18) pretrained on massive datasets (ImageNet) to accelerate learning on specialized tasks."},
            {"name": "Backbone Freezing vs Fine-tuning", "description": "Locking early layers (feature extractors) and tuning only final layers (classifiers) to prevent overfitting on tiny datasets."}
        ],
        "math_formulas": [
            {
                "name": "Cosine Similarity",
                "equation": "\\text{Cosine}(A, B) = \\frac{A \\cdot B}{||A|| \\cdot ||B||}",
                "variables": {"A, B": "High-dimensional feature representation vectors"},
                "purpose": "Measures the angular similarity between feature embeddings, ignoring vector scale bias."
            }
        ],
        "functions": [
            {
                "name": "classify_with_prototypes",
                "description": "Classifies query vectors by finding the closest class prototype via cosine similarity.",
                "real_world": "Enables zero-shot and few-shot classification in retrieval setups like face recognition or pathology searches.",
                "importance": "Bridges visual classification to geometric vector space matching."
            }
        ],
        "pitfalls": [
            {"name": "Catastrophic Forgetting", "description": "Using a high learning rate on unfrozen backbones overwrites general pretrained weights, ruining feature retrieval capabilities."},
            {"name": "Normalization Mismatch", "description": "Medical scans require specialized pixel transforms. Applying raw ImageNet means directly onto X-rays can wipe out critical visual features."}
        ]
    },
    "semantic_segmentation": {
        "core_concepts": [
            {"name": "Dense Prediction Decoders", "description": "Rebuilding spatial maps from compressed features. Instead of flat category labels, we output pixel-wise classification maps."},
            {"name": "Upsampling (Transpose Convolutions)", "description": "Learned upsampling layers that expand feature resolutions by reversing pooling operations."}
        ],
        "math_formulas": [
            {
                "name": "Soft Dice Loss Optimization",
                "equation": "L_{Dice} = 1 - \\frac{2 \\sum (p_i \\cdot g_i) + \\epsilon}{\\sum p_i^2 + \\sum g_i^2 + \\epsilon}",
                "variables": {"p_i": "Soft predicted pixel probability value", "g_i": "Binary ground-truth mask pixel", "\\epsilon": "Smoothing numerator safety"},
                "purpose": "Optimizes region boundary overlaps directly, ignoring background/foreground imbalances."
            }
        ],
        "functions": [
            {
                "name": "find_optimal_threshold",
                "description": "Searches probability thresholds to convert prediction scores into binary masks.",
                "real_world": "Calibrates model outputs to balance false positives and false negatives in medical diagnostics.",
                "importance": "Connects soft mathematical losses to hard clinical evaluation metrics."
            }
        ],
        "pitfalls": [
            {"name": "Class Imbalance Bias", "description": "Using standard BCE on tiny lesions causes the model to predict background pixels everywhere, yielding high accuracy but useless recall. Always mix in Dice Loss."},
            {"name": "Boundary Contours Blurring", "description": "Upsampling decoders scale features back up, but discard sharp details. U-Net skip connections are required to preserve high-frequency borders."}
        ]
    },
    "explainable_ai": {
        "core_concepts": [
            {"name": "Feature Attribution Map", "description": "Exposing the internal activations of a model to visualize exactly which pixels influenced its predictions."},
            {"name": "Grad-CAM (Gradient Class Activation Mapping)", "description": "Uses gradients flowing back to the final convolutional layer to weigh feature channel importances, projecting attention maps."}
        ],
        "math_formulas": [
            {
                "name": "Grad-CAM Weight Formulation",
                "equation": "\\alpha_c^k = \\frac{1}{Z} \\sum_{i,j} \\frac{\\partial Y^c}{\\partial A_{i,j}^k}, \\quad L^c = \\text{ReLU}\\left(\\sum_k \\alpha_c^k A^k\\right)",
                "variables": {"Y^c": "Logit prediction for class c", "A_{i,j}^k": "Activation of channel k at spatial location (i,j)", "\\alpha_c^k": "Attribution weight of channel k", "L^c": "Final Grad-CAM heatmap"},
                "purpose": "Calculates exactly which convolutional feature channels were positive drivers for the classification outcome."
            }
        ],
        "functions": [
            {
                "name": "test_class_switch_stability",
                "description": "Compares attributions for Class A vs. Class B on a single image.",
                "real_world": "Confirms explanations are query-sensitive (e.g. verifying the model looks at different visual structures when diagnosing nevus vs. melanoma).",
                "importance": "Proves attributions reflect class boundaries, not general image textures."
            }
        ],
        "pitfalls": [
            {"name": "Gradient Saturation", "description": "When models are confident, logits saturate, leading to vanishingly small gradients and flat, noisy attributions."},
            {"name": "Explanation Causal Fallacy", "description": "Assuming attributions represent biological guarantees. Grad-CAM shows where the model looked, not if its medical logic is correct."}
        ]
    },
    "vector_embeddings": {
        "core_concepts": [
            {"name": "Latent Space Compression", "description": "Representing raw inputs as coordinate points in a lower-dimensional semantic space. Here, direction encodes meaning and categories cluster naturally."},
            {"name": "Semantic Vector Search", "description": "Matching queries to database items by calculating angles between vectors, bypassing slow pixel searches."}
        ],
        "math_formulas": [
            {
                "name": "Euclidean Coordinate Distance",
                "equation": "d(A, B) = \\sqrt{\\sum_{i=1}^D (A_i - B_i)^2}",
                "variables": {"A_i, B_i": "Coordinate values along dimension i", "D": "Total dimensions of embedding"},
                "purpose": "Calculates absolute geometric distance between representation points."
            }
        ],
        "functions": [
            {
                "name": "compute_euclidean_distance",
                "description": "Calculates spatial Euclidean coordinates distance between two vectors.",
                "real_world": "Measures similarity in multi-class clustering setups, locating neighboring diagnostic samples.",
                "importance": "Acts as the baseline metric for coordinate space clustering."
            }
        ],
        "pitfalls": [
            {"name": "Curse of Dimensionality", "description": "In high-dimensional spaces (e.g. 512 dimensions), Euclidean distances concentrate, making all points seem equidistant. Always normalize and use Cosine instead."},
            {"name": "PCA for Retrieval", "description": "Confusing PCA projections as search environments. Projecting vectors down to 2D discards critical semantic data. Always search in the original high-dimensional space."}
        ]
    },
    "vlm_diagnostics": {
        "core_concepts": [
            {"name": "Multi-modal Alignment", "description": "Shared token spaces allowing models to project images and text into a unified representation layer (e.g. text tokens align with visual features)."},
            {"name": "Autoregressive generation", "description": "Generating diagnostics rationales word-by-word, conditioned on both system prompts and image tokens."}
        ],
        "math_formulas": [
            {
                "name": "Autoregressive Sequence Probability",
                "equation": "P(W \\mid I) = \\prod_{t=1}^T P(w_t \\mid w_{<t}, I)",
                "variables": {"I": "Visual image tokens", "w_t": "Generated word at step t", "w_{<t}": "Context words generated previously"},
                "purpose": "Calculates conditional probabilities for producing the next text diagnostic token."
            }
        ],
        "functions": [
            {
                "name": "extract_vlm_predictions_with_regex",
                "description": "Parses free-form model paragraphs to extract decisions and confidence metrics using regular expressions.",
                "real_world": "Structures conversational model summaries into standard digital records databases.",
                "importance": "Bridges unstructured natural language to downstream databases."
            }
        ],
        "pitfalls": [
            {"name": "Model Hallucinations", "description": "VLMs can generate confident but completely fabricated rationales. Output validation rules are required."},
            {"name": "Parsing Format Exceptions", "description": "Free-form generators can alter sentence layouts, causing regex matches to fail silently. Robust defaults are required."}
        ]
    },
    "gradio_deployment": {
        "core_concepts": [
            {"name": "Model Inference Handlers", "description": "Setting up dedicated request entrypoints that receive raw input shapes, normalize them, run model passes, and return visual metrics."},
            {"name": "Client-Server Web Architectures", "description": "Building clean web pages where clinicians can interact with models without needing terminal access."}
        ],
        "math_formulas": [
            {
                "name": "Inference Image Normalization",
                "equation": "I_{norm} = \\frac{I / 255.0 - \\mu}{\\sigma}",
                "variables": {"I": "Raw pixel array", "\\mu": "ImageNet channel mean vector", "\\sigma": "ImageNet channel standard deviation vector"},
                "purpose": "Standardizes raw user-uploaded image ranges to match model training weights."
            }
        ],
        "functions": [
            {
                "name": "get_image_pixel_statistics",
                "description": "Calculates pixel stats (mean, std, min, max) of client-uploaded images.",
                "real_world": "Runs validation checks to catch corrupt, low-contrast, or corrupted uploads before triggering model forward passes.",
                "importance": "Protects prediction models from corrupted user data."
                    }
                ],
                "pitfalls": [
                    {"name": "Port Address Conflicts", "description": "Attempting to launch a server on a port that is already in use crashes deployment scripts. Dynamic port checking is recommended."},
                    {"name": "Thread-Unsafe Inference", "description": "Concurrent server requests modifying global model parameters can corrupt predictions. Always run inference in thread-safe contexts."}
                ]
            }
        }
