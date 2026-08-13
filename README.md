# DigitalAgEdu

An AI-driven educational framework that integrates automated curriculum generation with an end-to-end computer vision pipeline, enabling experiential AI literacy learning for K-12 through realworld datasets

**Tags:** `Digital-Agriculture` `AI4CI` `Foundation-AI` `Visual-Analytics` `Kubernetes` `Nautilus` `HPC`

---

## License & Acknowledgements

This project is licensed under the MIT License.

```markdown
This project was developed as a Master's thesis at The Ohio State University (Systems and AI Lab, advised by Dr. Hari Subramoni), subsequently submitted to and implemented as part of the AI Presidential Challenge, and integrated with the NSF-funded ICICLE AI Institute.

National Science Foundation (NSF) funded AI institute for Intelligent Cyberinfrastructure with Computational Learning in the Environment (ICICLE) (OAC 2112606)

Additional thanks to Dr. Shearer Scott and Dr. Lisa Abrams for domain expertise, dataset access, and educator feedback, and to the Columbus School for Girls for pilot deployment support.
```

---

## 1. Project Philosophy & System Overview

Traditional AI education tools often present machine learning as a "black box" or use simplified, clean datasets that fail to reflect how real-world systems behave. DigitalAgEdu operates on the core principle: **"The Pipeline is the Curriculum."**

Students run a multi-stage computer vision pipeline on a dataset of their choice, then build, test, and explain the exact stages they executed through dynamically generated coding exercises.

```
       Image Dataset (Any Domain)
                    │
                    ▼
    [1] Image Acquisition        (Folder and validation checks)
                    │
                    ▼
    [2] DINOv2 Classification    (Fine-tuning transfer learning on custom classes)
                    │
                    ▼
    [3] SAM Segmentation         (Region-of-interest mask extraction)
                    │
                    ▼
    [4] Phi-3-Vision VLM         (Multimodal reasoning explanations)
                    │
                    ▼
    [5] Curriculum & Exercises   (Dynamic output generation based on run metrics)
```

By parameterizing domain names, directory paths, and labels from dataset metadata, the framework is **completely domain-agnostic**. The engine automatically adapts the syllabus and student coding challenges to fit the domain.

---

## 2. Repository Structure

```
curriculum_generator/
├── digitalagedu/
│   ├── core/                  # Curriculum generation engine
│   │   ├── config.py          # YAML config ingestion and validation schemas
│   │   ├── curriculum_service.py # Chronological sequence mapping & activity scheduler
│   │   ├── dataset_scanner.py # scans dataset folder to estimate visual complexity
│   │   ├── metrics.py         # Precision, Recall, F1, and AUC-ROC calculators
│   │   ├── orchestrator.py    # Master syllabus compiler
│   │   ├── practice_generator.py # Student exercise extractor and test harness
│   │   └── renderer.py        # Jinja2 markdown parser
│   └── templates/             # Master coding templates (walkthrough, warmup, exercises)
├── curriculum_resources/      # Active pipeline modules
│   ├── week_08/               # Classification solution (DINOv2)
│   ├── week_09/               # Segmentation solution (SAM)
│   └── week_11/               # VisionQA solution (Phi-3-Vision)
├── cluster_jobs/              # Standard SLURM scripts for OSC clusters
│   ├── run_cardinal.sh
│   ├── run_hurricane.sh
│   └── run_skin_cancer.sh
├── Dockerfile                 # Docker image spec compiling PyTorch, CUDA, and dependencies
├── entrypoint.sh              # Container startup script
├── pvc.yaml                   # Kubernetes PersistentVolumeClaim manifest
├── job.yaml                   # Kubernetes Job manifest
├── run_pipeline.py            # Main pipeline orchestrator script
├── food_nautilus.yaml         # Dataset configuration file mapped to Nautilus paths
└── README.md
```

---

## 3. How to Run the AI Pipeline

### A. Deploying on OSC Clusters (Tapis Portal / Apptainer)

The pipeline is registered as a batch application (`digital-age-edu`) on the ICICLE Tapis tenant. This allows you to launch runs dynamically from your web browser without logging into a terminal:

#### Method 1: Launch via the Tapis UI (Primary)

1. **Access the Tapis Portal:** Navigate to your Tapis UI workspace.
2. **Submit a Job:**
   * **App ID:** `digital-age-edu`
   * **Queue:** `nextgen` (1 Node, 12 Cores, charges to account `-A PAS2699`)
   * **GPU Allocation:** `--gpus-per-node=1` (with `--nv` container arg bound to enable CUDA acceleration)
   * **Arguments:** Pass the absolute path to your configuration file (e.g., `/fs/ess/PAS2699/mhole/curriculum_generator/food_config.yaml`) as the `config_file` app argument.
3. **Monitor & Download:** Once finished, download the generated exercises, syllabus, and outputs directly from the Tapis Jobs output browser mapping to your execution folder:
   `/fs/scratch/PAS2699/harvest_jobs/${JobUUID}/output`

#### Method 2: Launch via the OSC Terminal (CLI Fallback)

If you prefer running directly from the OSC login terminal using standard SLURM submissions:

1. **Submit the batch job:**

   ```bash
   sbatch cluster_jobs/run_cardinal.sh
   ```

2. **Monitor job status:**

   ```bash
   squeue -u $USER
   ```

### B. Deploying on NRP Nautilus (Kubernetes)

To run the full pipeline on a GPU-enabled Kubernetes cluster like NRP Nautilus:

1. **Verify your PVC is bound:**

   ```bash
   kubectl apply -f pvc.yaml
   kubectl get pvc -n sailab
   ```

2. **Copy your configuration file onto the persistent storage volume:**
   Start a temporary helper pod (`data-loader`) that mounts the PVC, upload your config file, and delete the helper to release the write lock:

   ```bash
   kubectl run data-loader --image=ubuntu -n sailab --restart=Never --overrides='{"spec": {"volumes": [{"name": "data", "persistentVolumeClaim": {"claimName": "sailab-data-pvc"}}], "containers": [{"name": "loader", "image": "ubuntu", "command": ["sleep", "infinity"], "volumeMounts": [{"name": "data", "mountPath": "/data"}]}]}}'
   
   kubectl cp food_nautilus.yaml data-loader:/data/food_nautilus.yaml -n sailab
   
   kubectl delete pod data-loader -n sailab
   ```

3. **Launch the batch Job:**

   ```bash
   kubectl apply -f job.yaml
   ```

4. **Tail the live logs directly from the PVC:**
   All execution console print statements are redirected directly onto the storage volume to prevent log loss when pods terminate:

   ```bash
   kubectl get pods -n sailab -l job-name=digital-age-edu-pipeline
   kubectl exec -it <pod-name> -n sailab -- tail -f /data/pipeline_execution.log
   ```

---

## 4. Output Artifacts & Student Curriculum

After the pipeline finishes running successfully, it outputs the following artifacts into the directory configured in your YAML file (e.g., `outputs/food_v1/`):

1. **`curriculum.json`:** The raw structured data containing course information, week-by-week goals, and learning outcomes.
2. **`curriculum_grade_x.md`:** A formatted Markdown syllabus containing lesson timelines, prerequisites, evaluation stats, and case study files.
3. **`results.csv`:** Tabular execution logs mapping image paths, ground truths, model predictions, and confidence distributions.
4. **`exercises/`:** Dynamically compiled weekly student directories (e.g., `Week_01`, `Week_02`, etc.) containing coding worksheets.

---

## 5. Working with Student Exercises

Each weekly exercise folder generated under your outputs directory contains the following student-facing assets:

* **`[topic]_exercise.py`:** Student skeleton files containing stubs, `# TODO` markers, and `# [REFERENCE_SOLUTION]` boundaries.
* **`[topic]_solution.py`:** Pre-compiled reference solutions for educators.
* **`[topic]_test.py`:** Cheat-proof unit test suites asserting logic, array outputs, and correct shapes.
* **`concepts.md`:** Detailed explanation of the week's system features and mathematical models.
* **`resource.md`:** Curated links, videos, and articles for independent reading.

### Running Reference Solutions & Tests

To verify all solution templates run and pass their test suites sequentially on the OSC cluster:

* **To run all solutions sequentially (Bash Loop):**

  ```bash
  for dir in outputs/food_v1/exercises/Week_*; do [ -d "$dir" ] && echo "=== Running $dir ===" && cd "$dir" && python *_solution.py && cd - > /dev/null; done
  ```

* **To execute unit tests directly:**

  ```bash
  cd outputs/food_v1/exercises/Week_01
  python numpy_basics_test.py
  ```

---

## 6. Swapping Dataset Domains

To apply this pipeline and generate a custom curriculum for a new domain:

1. Arrange your images in a standard folder-per-class layout:

   ```
   my_dataset/
   ├── class_name_1/
   │   ├── img001.jpg
   │   └── img002.jpg
   └── class_name_2/
       └── img001.jpg
   ```

2. Create a new `.yaml` configuration file mapping your dataset path and custom metadata (subject title, topics, grade level, and external resources).
3. Run the pipeline pointing to your new configuration. The engine will scan the dataset properties, calculate class imbalances and dataset complexity, and output a completely tailored learning package.
