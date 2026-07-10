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
        {"name": "Understanding Convolutional Layers in PyTorch", "url": "https://pytorch.org/docs/stable/generated/torch.nn.Conv2d.html", "description": "Mathematical specifications of multi-channel 2D convolutions, stride, and padding configurations."}
    ],
    "cnn_optimization": [
        {"name": "Understanding BatchNorm and Dropout in PyTorch", "url": "https://pytorch.org/docs/stable/generated/torch.nn.BatchNorm2d.html", "description": "Official parameter details explaining training vs validation execution shifts."},
        {"name": "PyTorch Saving & Loading Model Checkpoints Guide", "url": "https://pytorch.org/tutorials/beginner/saving_loading_models.html", "description": "Best practices for writing checkpoint state dicts containing weights, optimizers, and learning rate metadata."},
        {"name": "Understanding Learning Rate Schedulers", "url": "https://pytorch.org/docs/stable/optim.html", "description": "Visualizing step decay, cosine annealing, and custom dynamic schedule parameters."}
    ],
    "transfer_learning": [
        {"name": "PyTorch Transfer Learning Tutorial", "url": "https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html", "description": "Code patterns showing how to load pretrained backbones and configure feature extractor freezes."},
        {"name": "A Visual Guide to ResNet Architectures", "url": "https://towardsdatascience.com/an-illustrated-guide-to-resnet-5cf9b3ad40bf", "description": "Detailed breakdowns explaining residual connections, bottleneck layers, and layer hierarchies."},
        {"name": "Hugging Face Hub Models", "url": "https://huggingface.co/models", "description": "Explore thousands of pretrained vision backbones covering ViTs, ConvNeXts, and ResNets."}
    ],
    "semantic_segmentation": [
        {"name": "U-Net: Convolutional Networks for Biomedical Image Segmentation", "url": "https://arxiv.org/abs/1505.04597", "description": "The seminal paper introducing U-Net architectures, contractive contracting paths, and skip connections."},
        {"name": "PyTorch Transpose Convolutions Visualized", "url": "https://github.com/vdumoulin/conv_arithmetic", "description": "Animations showcasing how transpose convolutions upscale features spatially."},
        {"name": "Understanding Dice and Jaccard Loss Metrics", "url": "https://towardsdatascience.com/metrics-to-evaluate-your-semantic-segmentation-model-6bcb27863144", "description": "Detailed guides detailing mathematical formulations and code patterns for segmentation evaluation."}
    ],
    "explainable_ai": [
        {"name": "Grad-CAM: Visual Explanations from Deep Networks", "url": "https://arxiv.org/abs/1610.02391", "description": "The original academic paper defining Grad-CAM mathematical formulations and gradient weighting properties."},
        {"name": "PyTorch Autograd Backward Hooks Documentation", "url": "https://pytorch.org/docs/stable/generated/torch.nn.modules.module.register_module_backward_hook.html", "description": "API guide explaining how to register forward/backward hooks to intercept activation maps and gradients."},
        {"name": "Interpretability in Machine Learning (Book)", "url": "https://christophm.github.io/interpretable-ml-book/", "description": "Outstanding free textbook detailing Grad-CAM, Saliency, Integrated Gradients, and LIME."}
    ],
    "vector_embeddings": [
        {"name": "Vector Embeddings Explained", "url": "https://jalammar.github.io/illustrated-word2vec/", "description": "Intuitive visual guides showcasing how concepts map to direction and proximity in high-dimensional space."},
        {"name": "Visualizing High-Dimensional Data (t-SNE & PCA)", "url": "https://distill.pub/2016/misread-tsne/", "description": "Interactive web layouts detailing how projection models compress and cluster vector spaces."},
        {"name": "Pinecone: What is Vector Search?", "url": "https://www.pinecone.io/learn/vector-search/", "description": "Full-stack guide explaining indices, cosine metrics, Euclidean bounds, and similarity searches."}
    ],
    "gradio_deployment": [
        {"name": "Official Gradio Quickstart Guide", "url": "https://www.gradio.app/guides/quickstart", "description": "Learn to construct interface components, configure server backends, and run local diagnostic apps."},
        {"name": "HuggingFace Spaces Deployment Portal", "url": "https://huggingface.co/docs/hub/spaces-sdks-gradio", "description": "Hosting your Gradio web applications on public cloud servers for free."},
        {"name": "Building Interactive AI Web Interfaces in Python", "url": "https://realpython.com/gradio-python/", "description": "Full-stack introduction to building interactive front-ends for machine learning models."}
    ]
}

CONCEPT_GUIDES = {
    "numpy_basics": {
        "core_concepts": [
            {
                "name": "Multidimensional Arrays (Ndarrays)",
                "description": (
                    "NumPy arrays are homogeneous, grid-like data structures that store numerical values in contiguous blocks of memory. "
                    "In computer vision, images are represented as 3D matrices of shape $(Height, Width, Channels)$:\n\n"
                    "#### Image Pixel Grid Structure:\n"
                    "```text\n"
                    "Row 0: [R,G,B] [R,G,B] ... [R,G,B]\n"
                    "Row 1: [R,G,B] [R,G,B] ... [R,G,B]\n"
                    "...\n"
                    "Row H: [R,G,B] [R,G,B] ... [R,G,B]\n"
                    "```\n\n"
                    "By using contiguous memory, NumPy allows fast hardware-level data retrieval, which is essential when processing "
                    "millions of pixel values in real time."
                )
            },
            {
                "name": "Vectorization and Broadcasting",
                "description": (
                    "Vectorization replaces explicit Python `for` loops with compiled C-level operations that run directly on the CPU "
                    "using SIMD (Single Instruction, Multiple Data) hardware instructions.\n\n"
                    "**Broadcasting** defines rules for performing arithmetic operations on arrays of mismatched shapes. "
                    "A smaller array is mathematically 'broadcast' (stretched without copying memory) across a larger array to match shapes:\n"
                    "- Input Image: `(224, 224, 3)`\n"
                    "- Mean Vector: `(3,)` $\\rightarrow$ Stretched to `(224, 224, 3)` automatically.\n"
                    "- Multiplying them channel-wise is done instantly at the C-level without copying memory."
                )
            }
        ],
        "math_formulas": [
            {
                "name": "Z-Score Matrix Normalization",
                "equation": "Z_i = \\frac{x_i - \\mu}{\\sigma}",
                "variables": {
                    "x_i": "Original numerical value at pixel coordinate i.",
                    "\\mu": "The mean value of all coordinates in the matrix/channel.",
                    "\\sigma": "The standard deviation of all coordinates in the matrix/channel."
                },
                "purpose": (
                    "Standardizes the input feature distributions to have a mean of 0 and a standard deviation of 1. "
                    "In neural networks, normalizing pixel bounds prevents early gradient scaling anomalies and ensures "
                    "stable, predictable weight optimization."
                )
            }
        ],
        "functions": [
            {
                "name": "statistics_and_standardization",
                "description": "Calculates matrix-wide statistics (mean, std, min, max) and standardizes the array.",
                "real_world": "Prepares dataset inputs by smoothing out lighting and exposure variations across different scanners.",
                "importance": (
                    "#### Step-by-Step Algorithm Workflow:\n"
                    "1. Compute the mean of the input array: $\\mu = \\frac{1}{N} \\sum x_i$.\n"
                    "2. Compute the standard deviation: $\\sigma = \\sqrt{\\frac{1}{N} \\sum (x_i - \\mu)^2}$.\n"
                    "3. Subtract the mean and divide by standard deviation for every pixel element.\n"
                    "4. Clip values to prevent extreme outliers from destabilizing training parameters."
                )
            },
            {
                "name": "extract_patches",
                "description": "Extracts overlapping or non-overlapping localized 2D patches from an image using stride parameters.",
                "real_world": "Extracts regions of interest from massive pathology scans (Gigapixel WSIs) that exceed GPU memory limits.",
                "importance": (
                    "Slices massive images into uniform sub-matrices to train target classification networks on localized "
                    "textures and sub-patterns."
                )
            }
        ],
        "pitfalls": [
            {
                "name": "Looping Over Pixels",
                "description": (
                    "Using Python `for y in range(H):` loops to process pixels creates an interpreter translation bottleneck. "
                    "Always use vectorized operations (e.g. `img - mean`) to trigger compiled C-level execution."
                )
            },
            {
                "name": "Memory Copy vs. View Confusion",
                "description": (
                    "NumPy slicing creates a 'view' of the original array's memory, not a copy. Modifying a slice (view) "
                    "will silently modify the original image. Use `array.copy()` when modifications must be kept separate."
                )
            }
        ]
    },
    "pandas_analytics": {
        "core_concepts": [
            {
                "name": "Tabular Data Structures",
                "description": (
                    "Pandas DataFrames model relational data (tables) in Python. In machine learning pipelines, "
                    "tabular structures are essential for storing prediction logs, confidence histories, and training metadata."
                )
            },
            {
                "name": "Active Learning & Failure Mining",
                "description": (
                    "By sorting and filtering prediction logs, we identify cases where the model made incorrect classifications "
                    "with high confidence. We feed these 'hard negative' images back into the next training loop. "
                    "This active learning workflow targets annotation efforts directly at the model's blind spots."
                )
            }
        ],
        "math_formulas": [
            {
                "name": "Classification Accuracy Rate",
                "equation": "\\text{Accuracy} = \\frac{TP + TN}{TP + TN + FP + FN}",
                "variables": {
                    "TP": "True Positives (actual positive predicted as positive)",
                    "TN": "True Negatives (actual negative predicted as negative)",
                    "FP": "False Positives (actual negative predicted as positive)",
                    "FN": "False Negatives (actual positive predicted as negative)"
                },
                "purpose": "Calculates the global percentage of correct classification decisions across the entire logged evaluation run."
            }
        ],
        "functions": [
            {
                "name": "handle_missing_values",
                "description": "Fills missing values (NaNs) in the prediction confidence records using a default or mean value.",
                "real_world": "Cleans incomplete datasets, preventing pipeline execution halts from null values.",
                "importance": "Ensures downstream models receive clean, fully populated tensors."
            },
            {
                "name": "find_hardest_samples",
                "description": "Filters and sorts predictions to isolate misclassified images with high confidence scores.",
                "real_world": "Automates active learning by flagging the model's most critical blind spots for human verification.",
                "importance": (
                    "#### Step-by-Step Workflow:\n"
                    "1. Isolate incorrect predictions: `df[df['ground_truth'] != df['predicted_class']]`.\n"
                    "2. Sort the incorrect samples by confidence descending: `.sort_values('confidence', ascending=False)`.\n"
                    "3. Extract the top $K$ worst mistakes for detailed debugging."
                )
            }
        ],
        "pitfalls": [
            {
                "name": "SettingWithCopyWarning",
                "description": (
                    "Attempting to modify a filtered slice of a DataFrame throws warnings and can fail silently. "
                    "Always use `.loc[row_indexer, col_indexer]` to make modifications in-place on the original DataFrame."
                )
            },
            {
                "name": "Data Leakage",
                "description": (
                    "Using validation/test distributions to impute training NaNs leaks statistics, yielding overly optimistic results."
                )
            }
        ]
    },
    "pytorch_basics": {
        "core_concepts": [
            {
                "name": "Tensors & Autograd Graph Trace",
                "description": (
                    "PyTorch Tensors are multi-dimensional arrays optimized for GPU acceleration. PyTorch builds a dynamic "
                    "directed acyclic graph (DAG) during the forward pass. Every mathematical operation creates a node linking "
                    "inputs to outputs. When `loss.backward()` is called, PyTorch traverses this graph backward, automatically "
                    "computing derivatives via the chain rule."
                )
            },
            {
                "name": "Multi-Layer Perceptron (MLP) Lifecycle",
                "description": (
                    "An MLP consists of fully connected (dense) linear layers interspersed with activation functions (like ReLU) "
                    "to map inputs to decision logits. The training lifecycle follows a strict sequence: forward pass, loss calculation, "
                    "gradient reset, backpropagation, and weight update."
                )
            }
        ],
        "math_formulas": [
            {
                "name": "Binary Cross-Entropy (BCE) Loss",
                "equation": "L_{BCE} = -\\frac{1}{N} \\sum_{i=1}^N \\left[ y_i \\log(p_i) + (1 - y_i) \\log(1 - p_i) \\right]",
                "variables": {
                    "y_i": "Binary ground-truth label (0 or 1).",
                    "p_i": "Model's predicted probability of the positive class (output of sigmoid function)."
                },
                "purpose": (
                    "Measures classification error on probability outputs. Because of the log scale, BCE heavily penalizes "
                    "confident wrong answers, driving model updates to quickly adjust incorrect parameters."
                )
            },
            {
                "name": "L2 Weight Decay Regularization",
                "equation": "L_{total} = L_{BCE} + \\frac{\\lambda}{2} \\sum_{w} w^2",
                "variables": {
                    "\\lambda": "Regularization coefficient (weight decay factor).",
                    "w": "Learnable parameters (weights) of the network."
                },
                "purpose": (
                    "Adds a penalty proportional to the squared magnitude of network weights. This discourages large weights, "
                    "enforcing simpler decision boundaries and mitigating overfitting."
                )
            }
        ],
        "functions": [
            {
                "name": "train_step_with_l2",
                "description": "Executes a forward pass, manual L2 penalty calculation, backprop, and optimizer step.",
                "real_world": "Underpins model updates in training pipelines, keeping weight values small and generalized.",
                "importance": (
                    "#### Step-by-Step Training Step:\n"
                    "1. Reset gradients: `optimizer.zero_grad()`.\n"
                    "2. Forward pass: `predictions = model(inputs)`.\n"
                    "3. Loss computation: `loss = loss_fn(predictions, labels)`.\n"
                    "4. Add regularizer: Calculate L2 norm of weights and add to loss.\n"
                    "5. Backward pass: `loss.backward()` (calculates gradients).\n"
                    "6. Optimization: `optimizer.step()` (updates weights)."
                )
            }
        ],
        "pitfalls": [
            {
                "name": "Forgetting to Zero Gradients",
                "description": (
                    "In PyTorch, gradients accumulate. Skipping `optimizer.zero_grad()` mixes steps, causing weight explosions."
                )
            },
            {
                "name": "Shape Mismatches during Forward Passes",
                "description": (
                    "Linear layers require exact matrix multiplications. Mismatched hidden dimensions throw compile errors."
                )
            }
        ]
    },
    "interactive_segmentation": {
        "core_concepts": [
            {
                "name": "Classical Image Segmentation",
                "description": (
                    "Grouping pixels into regions of interest based on color, edge density, or seed similarity without deep learning. "
                    "Classic thresholding algorithms (like FloodFill) are fast, run entirely on CPU, and are useful for generating "
                    "initial binary masks."
                )
            },
            {
                "name": "OpenCV Interactive Event Listening",
                "description": (
                    "Connecting user actions (like mouse clicks) to processing triggers, allowing real-time segmentation tuning. "
                    "In headless cluster environments, we write fallbacks to bypass GUI window loops, running simulations at pre-defined seeds instead."
                )
            }
        ],
        "math_formulas": [
            {
                "name": "Spatial Image Moments & Centroids",
                "equation": "M_{ij} = \\sum_{x,y} x^i y^j I(x,y), \\quad cX = \\frac{M_{10}}{M_{00}}, \\quad cY = \\frac{M_{01}}{M_{00}}",
                "variables": {
                    "I(x,y)": "Binary pixel intensity at coordinate (x,y) (0 or 1).",
                    "M_{00}": "Total mass (area) of the binary mask.",
                    "cX, cY": "Coordinates of the geometric center of mass."
                },
                "purpose": "Calculates the geometric center of mass of a visual mask to track lesion shapes over time."
            }
        ],
        "functions": [
            {
                "name": "calculate_mask_centroid",
                "description": "Extracts spatial moments using `cv2.moments` to compute coordinates.",
                "real_world": "Tracks growth or coordinates of target structures over sequential frames.",
                "importance": "Provides coordinate alignments for cropping or spatial centering pipelines."
            }
        ],
        "pitfalls": [
            {
                "name": "Coordinate Axis Swapping",
                "description": (
                    "OpenCV uses $(X, Y)$ coordinate ordering, whereas NumPy matrix shapes are accessed as $(Row/Height, Col/Width)$. "
                    "Swapping these indexes leads to incorrect indexing and coordinate out-of-bounds crashes."
                )
            },
            {
                "name": "Moments Division By Zero",
                "description": (
                    "Dividing by $M_{00}$ on empty masks throws execution errors. A safety branch is required."
                )
            }
        ]
    },
    "image_datasets": {
        "core_concepts": [
            {
                "name": "Custom Datasets subclassing",
                "description": (
                    "Creating custom data interfaces that lazy-load single samples from directories, preventing GPU memory exhaustion. "
                    "PyTorch datasets override `__len__` to return the size of the dataset, and `__getitem__` to load a single sample."
                )
            },
            {
                "name": "Dataloader Batching & Threading",
                "description": (
                    "Orchestrates multi-processing queues, prefetching, and shuffling batches to feed the GPU training loop continuously. "
                    "It aggregates individual data tuples into a single batched tensor of shape $(BatchSize, Channels, Height, Width)$."
                )
            }
        ],
        "math_formulas": [
            {
                "name": "Dataset-Wide Channel Mean",
                "equation": "\\mu_c = \\frac{1}{N \\cdot H \\cdot W} \\sum_{i=1}^N \\sum_{y=1}^H \\sum_{x=1}^W I_c(i, y, x)",
                "variables": {
                    "I_c": "Pixel coordinate value of channel c.",
                    "N": "Total number of images in the dataset.",
                    "H, W": "Height and width dimensions."
                },
                "purpose": "Calculates reference statistics across all pixels to apply normalization transforms before training."
            }
        ],
        "functions": [
            {
                "name": "calculate_dataset_stats",
                "description": "Iterates over the dataset to calculate mean and standard deviation across channels.",
                "real_world": "Computes dataset-specific normalizations for unique medical images (e.g. grayscale X-rays vs RGB skin scans).",
                "importance": (
                    "#### Step-by-Step Statistics Aggregator:\n"
                    "1. Accumulate raw sum of pixels channel-wise: $S_c = \\sum I_c$.\n"
                    "2. Divide by the total pixel footprint ($N \\times H \\times W$) to get the mean $\\mu_c$.\n"
                    "3. Accumulate squared difference sum: $D_c = \\sum (I_c - \\mu_c)^2$.\n"
                    "4. Compute standard deviation: $\\sigma_c = \\sqrt{\\frac{D_c}{N \\times H \\times W}}$."
                )
            }
        ],
        "pitfalls": [
            {
                "name": "Blocking Lazy-Loading Disk I/O",
                "description": (
                    "Performing expensive transformations (like disk resizing) inside `__getitem__` stalls the pipeline. Always pre-process or optimize raw files."
                )
            },
            {
                "name": "Shuffling Validation Sets",
                "description": (
                    "Shuffling validation or test sets is useless, wastes compute, and ruins index comparisons."
                )
            }
        ]
    },
    "custom_cnn": {
        "core_concepts": [
            {
                "name": "Convolutional Operations",
                "description": (
                    "Applying small sliding spatial filters (kernels) over feature matrices to capture edges, textures, and shapes. "
                    "Unlike MLPs, convolutions preserve spatial locality and dramatically reduce parameter counts via weight sharing."
                )
            },
            {
                "name": "Downsampling (Pooling)",
                "description": (
                    "Reduces resolution while preserving core features, extending receptive fields and lowering overall parameter sizes."
                )
            }
        ],
        "math_formulas": [
            {
                "name": "Output Dimension Shape Logic",
                "equation": "O = \\lfloor \\frac{I - K + 2P}{S} \\rfloor + 1",
                "variables": {
                    "I": "Input dimension spatial size (Height or Width).",
                    "K": "Kernel/filter dimension size.",
                    "P": "Padding size applied to borders.",
                    "S": "Stride step size."
                },
                "purpose": "Traces how image spatial resolutions contract across successive network layers."
            },
            {
                "name": "Conv Layer Parameters Count",
                "equation": "\\text{Params} = C_{out} \\cdot (C_{in} \\cdot K^2 + 1)",
                "variables": {
                    "C_{in}": "Input channel count.",
                    "C_{out}": "Output channel count.",
                    "K": "Kernel spatial dimension."
                },
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
            {
                "name": "Flatten Dims Over-reduction",
                "description": (
                    "Over-pooling input matrices down to zero throws parameter shape exceptions during fully connected flatten stages."
                )
            },
            {
                "name": "Incorrect Padding Configuration",
                "description": (
                    "Forgetting padding causes spatial dimensions to shrink rapidly, discarding boundary features in early layers."
                )
            }
        ]
    },
    "cnn_optimization": {
        "core_concepts": [
            {
                "name": "Batch Normalization (BatchNorm)",
                "description": (
                    "Normalizes layer inputs per batch during training. This stabilizes activations, mitigates internal covariate shift, and allows higher learning rates."
                )
            },
            {
                "name": "Dropout Regularization",
                "description": (
                    "Randomly deactivates neurons during training. This forces the network to learn redundant representations, preventing reliance on spurious correlations."
                )
            }
        ],
        "math_formulas": [
            {
                "name": "Step Learning Rate Decay",
                "equation": "\\eta_t = \\eta_0 \\cdot \\gamma^{\\lfloor t / s \\rfloor}",
                "variables": {
                    "\\eta_t": "Learning rate at epoch t.",
                    "\\eta_0": "Initial learning rate.",
                    "\\gamma": "Decay factor (e.g. 0.1).",
                    "s": "Step size decay interval."
                },
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
            {
                "name": "Eval Mode Swapping Skip",
                "description": (
                    "Failing to switch to `model.eval()` before validation leaves Dropout active and BatchNorm updating, ruining inference predictions."
                )
            },
            {
                "name": "Partial State Restores",
                "description": (
                    "Loading checkpoints with layers that have different shapes silently bypasses updates, leaving target weights untrained."
                )
            }
        ]
    },
    "transfer_learning": {
        "core_concepts": [
            {
                "name": "Pretrained Backbone Benchmarking",
                "description": (
                    "Using deep neural networks (like ResNet18 or ResNet50) that have been pre-trained on massive datasets "
                    "(such as ImageNet, containing over 14 million everyday images across 1,000 object categories) to serve as "
                    "reusable feature extractors for a new, specialized target domain.\n\n"
                    "#### The Hierarchy of Feature Maps:\n"
                    "Deep learning models do not process images as flat pixels; they construct hierarchical understandings:\n"
                    "- **Early Layers:** Learn generic visual primitives: Gabor-like filters, edge orientations, corners, and solid colors.\n"
                    "- **Mid Layers:** Combine primitives into compound textures, basic shapes (e.g., circular blobs, cross-hatching patterns).\n"
                    "- **Late Layers:** Construct specialized semantic objects (e.g., cat ears, car wheels).\n\n"
                    "Because early-layer features (edges and textures) are universal across all image classification tasks, we can reuse "
                    "these features for a new target task. This skips the resource-heavy step of learning primitive visual shapes from scratch.\n\n"
                    "#### The Piano vs. Organ Analogy:\n"
                    "If you already know how to play the piano (ImageNet), learning to play the pipe organ (your new target classification task) "
                    "is significantly faster than starting music lessons from scratch. Your fingers already have the motor coordination, muscle memory, "
                    "and understanding of musical notation. Similarly, a backbone model already knows how to detect visual structures; we just need to "
                    "teach it to map those structures to a new set of output categories."
                )
            },
            {
                "name": "Backbone Freezing vs Fine-tuning",
                "description": (
                    "When adapting a pre-trained model to a new task, we must choose which layers of weights are allowed to be updated by the optimizer:\n\n"
                    "- **Backbone Freezing:** We lock the weights of all feature extraction layers (`requires_grad = False`). Only the weights of the final "
                    "classification layer (e.g., the fully connected linear layer) are updated during training.\n"
                    "  - *Why:* Essential when target datasets are tiny (under 100 images). If we try to train millions of backbone weights on a tiny dataset, "
                    "the model will immediately overfit and memorize the noise in the training set.\n"
                    "- **Fine-Tuning:** We keep the feature extraction weights trainable (`requires_grad = True`) but train them with a highly reduced learning "
                    "rate. This allows the pre-trained weights to shift slightly to adapt to the shapes of the new domain.\n"
                    "- **Discriminative Fine-Tuning:** We freeze the early feature layers (which extract simple edges) and unfreeze only the late convolutional blocks "
                    "(like `layer4` in ResNet18). This customizes high-level textures while preserving generic visual primitives.\n\n"
                    "#### Feature Weight Propagation Flow:\n"
                    "```text\n"
                    "[Input Image] ───► [Frozen Backbone (Layer1->3)] ───► [Fine-Tuned Block (Layer4)] ───► [Trainable FC Classifier] ───► [Logits]\n"
                    "               (Weights locked: grad=False)           (Specialized shapes: grad=True)      (Class mapping: grad=True)\n"
                    "```"
                )
            }
        ],
        "math_formulas": [
            {
                "name": "Cosine Similarity & Scale Invariance",
                "equation": "\\text{Cosine}(A, B) = \\cos(\\theta) = \\frac{A \\\\cdot B}{\\|A\\| \\\\cdot \\|B\\|} = \\frac{\\sum_{i=1}^D A_i B_i}{\\sqrt{\\sum_{i=1}^D A_i^2} \\\\cdot \\sqrt{\\sum_{i=1}^D B_i^2}}",
                "variables": {
                    "A, B": "High-dimensional feature vectors (embeddings) of size D extracted by the backbone.",
                    "A \\cdot B": "The dot product, summing the element-wise multiplication of coordinate projections.",
                    "\\|A\\|, \\|B\\|": "The L2 norms (Euclidean lengths) of the feature representation vectors."
                },
                "purpose": (
                    "Measures the angular similarity between two feature embeddings in geometric space, completely ignoring "
                    "vector scale bias. In computer vision, Euclidean distance (L2 distance) is highly sensitive to changes in image "
                    "contrast, brightness, or color scale. If you make an image brighter, its embedding vector scales up (lengthens) "
                    "in space, causing L2 distance to flag a false difference. Cosine similarity only checks the direction/angle of the "
                    "vectors. If two images contain the same geometric features under different lighting, their vectors point in the "
                    "same direction, yielding a similarity close to 1.0."
                )
            }
        ],
        "functions": [
            {
                "name": "classify_with_prototypes",
                "description": (
                    "Computes the representative prototype vector for each class and classifies query embeddings by calculating "
                    "their proximity to these prototypes."
                ),
                "real_world": (
                    "Serves as the foundation for few-shot learning, metric learning, and large-scale image retrieval networks "
                    "(e.g., matching a face scan to a database of users, or searching a hospital archive for slides with similar "
                    "cellular structures)."
                ),
                "importance": (
                    "#### Step-by-Step Algorithm Workflow:\n"
                    "1. **Extract Support Embeddings:** Pass a small set of labeled sample images through the backbone feature extractor to "
                    "get their vector representations: $x_i \\in \\mathbb{R}^D$.\n"
                    "2. **Calculate Class Prototypes:** Compute the mean vector (the 'prototype' $P_c$) for each class $c$:\n"
                    "   $$P_c = \\frac{1}{N_c} \\sum_{i=1}^{N_c} x_i$$\n"
                    "3. **Extract Query Embedding:** Get the embedding $q \\in \\mathbb{R}^D$ for the unlabeled query image.\n"
                    "4. **Compute Proximities:** Calculate the cosine similarity between $q$ and each prototype:\n"
                    "   $$\\text{Score}_c = \\text{Cosine}(q, P_c)$$\n"
                    "5. **Assign Label:** Predict the class label with the highest similarity score:\n"
                    "   $$\\hat{y} = \\arg\\max_c \\text{Score}_c$$"
                )
            }
        ],
        "pitfalls": [
            {
                "name": "Catastrophic Forgetting",
                "description": (
                    "If you unfreeze the backbone feature extractor and train the entire network with a standard, high learning rate "
                    "(e.g., $10^{-3}$), the large gradients will overwrite the pre-trained ImageNet weights. The network will lose its "
                    "ability to detect general borders and shapes, destroying its performance on validation data. To prevent this, always "
                    "use a highly reduced learning rate (e.g., $10^{-5}$) for the backbone compared to the newly initialized classification head."
                )
            },
            {
                "name": "Preprocessing and Normalization Mismatch",
                "description": (
                    "Pre-trained backbones expect input images to be processed and normalized using the exact statistics of the dataset they "
                    "were trained on. For ImageNet, this means scaling images to $[0, 1]$ and normalizing channels with `mean=[0.485, 0.456, 0.406]` "
                    "and `std=[0.229, 0.224, 0.225]`. If you feed in images normalized to standard ranges, or apply gray-scale transforms, the "
                    "input feature distribution will shift, causing the backbone layers to output garbage features. Always align your preprocessing "
                    "transforms to match the backbone's pre-training configuration."
                )
            }
        ]
    },
    "semantic_segmentation": {
        "core_concepts": [
            {
                "name": "Dense Prediction Decoders",
                "description": (
                    "Rebuilding spatial maps from compressed features. Instead of flat category labels, we output pixel-wise classification maps. "
                    "In segmenting regions of interest, U-Net uses symmetric contraction and expansion pathways to retain details."
                )
            },
            {
                "name": "Upsampling (Transpose Convolutions)",
                "description": (
                    "Learned upsampling layers that expand feature resolutions by reversing pooling operations, rebuilding spatial details."
                )
            }
        ],
        "math_formulas": [
            {
                "name": "Soft Dice Loss Optimization",
                "equation": "L_{Dice} = 1 - \\frac{2 \\sum_{i=1}^N (p_i \\cdot g_i) + \\epsilon}{\\sum_{i=1}^N p_i^2 + \\sum_{i=1}^N g_i^2 + \\epsilon}",
                "variables": {
                    "p_i": "Soft predicted pixel probability value (output of Sigmoid activation).",
                    "g_i": "Binary ground-truth mask pixel value (0 or 1).",
                    "\\epsilon": "Smoothing factor to prevent division by zero and stabilize the gradients."
                },
                "purpose": (
                    "Optimizes region boundary overlaps directly. Standard Cross Entropy computes pixel-wise loss independently, "
                    "which biases the model when target objects are tiny. Dice Loss evaluates the global overlap area, ignoring background imbalances."
                )
            }
        ],
        "functions": [
            {
                "name": "find_optimal_threshold",
                "description": "Searches probability thresholds to convert prediction scores into binary masks.",
                "real_world": "Calibrates model outputs to balance false positives and false negatives in target segmentation tasks.",
                "importance": (
                    "#### Step-by-Step Search Workflow:\n"
                    "1. Evaluate a grid of candidate threshold values between $[0.1, 0.9]$.\n"
                    "2. Apply thresholding to create candidate binary masks.\n"
                    "3. Calculate the Jaccard index (IoU) between prediction and ground-truth.\n"
                    "4. Select the threshold yielding the highest average IoU."
                )
            }
        ],
        "pitfalls": [
            {
                "name": "Class Imbalance Bias",
                "description": (
                    "Using standard BCE on tiny targets causes the model to predict background pixels everywhere, yielding high accuracy but useless recall. Always mix in Dice Loss."
                )
            },
            {
                "name": "Boundary Contours Blurring",
                "description": (
                    "Upsampling decoders scale features back up, but discard sharp details. U-Net skip connections are required to preserve high-frequency borders."
                )
            }
        ]
    },
    "explainable_ai": {
        "core_concepts": [
            {
                "name": "Feature Attribution Map",
                "description": (
                    "Exposing the internal activations of a model to visualize exactly which pixels influenced its predictions."
                )
            },
            {
                "name": "Grad-CAM (Gradient Class Activation Mapping)",
                "description": (
                    "Uses gradients flowing back to the final convolutional layer to weigh feature channel importances, projecting attention maps."
                )
            }
        ],
        "math_formulas": [
            {
                "name": "Grad-CAM Weight Formulation",
                "equation": "\\alpha_c^k = \\frac{1}{Z} \\sum_{i,j} \\frac{\\partial Y^c}{\\partial A_{i,j}^k}, \\quad L^c = \\text{ReLU}\\left(\\sum_k \\alpha_c^k A^k\\right)",
                "variables": {
                    "Y^c": "Logit prediction score for class c.",
                    "A_{i,j}^k": "Activation of channel k at spatial location (i,j) in the target conv layer.",
                    "\\alpha_c^k": "Attribution weight indicating the importance of feature map channel k for class c.",
                    "L^c": "Final Grad-CAM visual heatmap."
                },
                "purpose": "Calculates exactly which convolutional feature channels were positive drivers for the classification outcome."
            }
        ],
        "functions": [
            {
                "name": "test_class_switch_stability",
                "description": "Compares attributions for Class A vs. Class B on a single image.",
                "real_world": "Confirms explanations are query-sensitive (e.g. verifying the model looks at different visual structures when diagnosing different target conditions).",
                "importance": (
                    "#### Verification Workflow:\n"
                    "1. Compute Grad-CAM map $L_A$ for target class A.\n"
                    "2. Compute Grad-CAM map $L_B$ for target class B.\n"
                    "3. Calculate the IoU between $L_A$ and $L_B$.\n"
                    "4. If IoU is low, the network's explanations are query-sensitive, confirming it evaluates features distinctively."
                )
            }
        ],
        "pitfalls": [
            {
                "name": "Gradient Saturation",
                "description": (
                    "When models are confident, logits saturate, leading to vanishingly small gradients and flat, noisy attributions."
                )
            },
            {
                "name": "Explanation Causal Fallacy",
                "description": (
                    "Assuming attributions represent biological guarantees. Grad-CAM shows where the model looked, not if its logic is correct."
                )
            }
        ]
    },
    "vector_embeddings": {
        "core_concepts": [
            {
                "name": "Latent Space Compression",
                "description": (
                    "Representing raw inputs as coordinate points in a lower-dimensional semantic space. Here, direction encodes meaning and categories cluster naturally."
                )
            },
            {
                "name": "Semantic Vector Search",
                "description": (
                    "Matching queries to database items by calculating angles between vectors, bypassing slow pixel searches."
                )
            }
        ],
        "math_formulas": [
            {
                "name": "Euclidean Coordinate Distance",
                "equation": "d(A, B) = \\sqrt{\\sum_{i=1}^D (A_i - B_i)^2}",
                "variables": {
                    "A_i, B_i": "Coordinate values along dimension i of vectors A and B.",
                    "D": "Total dimensions of the embedding space."
                },
                "purpose": "Calculates absolute geometric distance between representation points."
            }
        ],
        "functions": [
            {
                "name": "compute_euclidean_distance",
                "description": "Calculates spatial Euclidean coordinates distance between two vectors.",
                "real_world": "Measures similarity in multi-class clustering setups, locating neighboring diagnostic samples.",
                "importance": (
                    "#### Step-by-Step Distance Calculator:\n"
                    "1. Compute element-wise subtraction: $diff_i = A_i - B_i$.\n"
                    "2. Square all difference terms: $sq\\_diff_i = diff_i^2$.\n"
                    "3. Sum the squared differences: $sum\\_sq = \\sum sq\\_diff_i$.\n"
                    "4. Compute square root of the sum: $d = \\sqrt{sum\\_sq}$."
                )
            }
        ],
        "pitfalls": [
            {
                "name": "Curse of Dimensionality",
                "description": (
                    "In high-dimensional spaces (e.g. 512 dimensions), Euclidean distances concentrate, making all points seem equidistant. Always normalize and use Cosine instead."
                )
            },
            {
                "name": "PCA for Retrieval",
                "description": (
                    "Confusing PCA projections as search environments. Projecting vectors down to 2D discards critical semantic data. Always search in the original high-dimensional space."
                )
            }
        ]
    },
    "gradio_deployment": {
        "core_concepts": [
            {
                "name": "Model Inference Handlers",
                "description": (
                    "Setting up dedicated request entrypoints that receive raw input shapes, normalize them, run model passes, and return visual metrics."
                )
            },
            {
                "name": "Client-Server Web Architectures",
                "description": (
                    "Building clean web pages where clinicians can interact with models without needing terminal access."
                )
            }
        ],
        "math_formulas": [
            {
                "name": "Inference Image Normalization",
                "equation": "I_{norm} = \\frac{I / 255.0 - \\mu}{\\sigma}",
                "variables": {
                    "I": "Raw pixel array input (values in $[0, 255]$).",
                    "\\mu": "Mean vector used during target model pretraining.",
                    "\\sigma": "Standard deviation vector used during target model pretraining."
                },
                "purpose": "Standardizes raw user-uploaded image ranges to match model training weights."
            }
        ],
        "functions": [
            {
                "name": "get_image_pixel_statistics",
                "description": "Calculates pixel stats (mean, std, min, max) of client-uploaded images.",
                "real_world": "Runs validation checks to catch corrupt, low-contrast, or corrupted uploads before triggering model forward passes.",
                "importance": (
                    "#### Validation Protocol Workflow:\n"
                    "1. Extract raw image array statistics.\n"
                    "2. Check if the variance of values is near zero (indicates a blank, dark, or corrupted upload).\n"
                    "3. Raise ValueError if statistics indicate corrupted data, preventing useless model runs."
                )
            }
        ],
        "pitfalls": [
            {
                "name": "Port Address Conflicts",
                "description": (
                    "Attempting to launch a server on a port that is already in use crashes deployment scripts. Dynamic port checking is recommended."
                )
            },
            {
                "name": "Thread-Unsafe Inference",
                "description": (
                    "Concurrent server requests modifying global model parameters can corrupt predictions. Always run inference in thread-safe contexts."
                )
            }
        ]
    }
}
