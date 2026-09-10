Jason - You have a promising system, but the current paper reads more like an AI-pipeline description than an EduHiPC Research-to-Education paper. Your revision should make one idea unmistakable: the workflow itself is a source of reusable educational evidence—predictions, errors, metrics, resource traces, validation logs, and provenance records—not merely a backend used to generate generic lessons.
 
Here is the overleaf 0 Overleaf, Online LaTeX Editor
Overleaf, Online LaTeX Editor
An online LaTeX editor that’s easy to use. No installation, real-time collaboration, version control, hundreds of LaTeX templates, and more.
 
This is the workshop - https://cdercenter.org/eduhipc-2026/#tracks
EduHiPC-2026 – CDER
A post from admin on CDER provided by: https://cdercenter.org
 
frame the paper around this central claim:
Smart Curriculum Designer converts validated AI/HPC workflow artifacts into provenance-linked, role-specific learning modules that help learners understand, evaluate, reproduce, and contribute to computational research workflows.
 
 
 
Use this structure.
I. Research Workflows as Educational Resources
Explain the workflow-literacy gap.
State the central thesis.
Give your contribution list.
II. Artifact-to-Learning-Module Contract
Define artifact categories.
Define required provenance and validation fields.
Define module outputs and intended learner roles.
III. Smart Curriculum Designer Pipeline
Show architecture figure.
Explain research workflow, artifact packaging, generation, validation, and instructor control.
Keep software-stack details concise.
IV. Research-to-Education Case Study
Describe the AI/HPC workflow.
Show one detailed learning module.
Map modules to AI/HPC learning objectives.
Include the performance/telemetry module.
V. Validation and Lessons Learned
Artifact-grounded versus generic-context baseline, if completed.
Expert review and functional validation.
Failures and corrections.
Cross-domain demonstration, if completed.
Limitations.
VI. Conclusion
Re-state the narrow contribution:
“We make validated workflow evidence available as instructional material.”
Do not claim student learning gains.
Identify classroom deployment and long-term evaluation as future work.
 
In the abstract, do not begin with generic statements about AI becoming important in society. Start with the concrete education problem.
 
Suggested abstract structure
Problem: AI/HPC workflows create useful evidence, but that evidence is not normally transformed into teaching materials.
Gap: Learners often see final results or toy examples, not the predictions, errors, runtime behavior, validation records, and provenance that shape real workflow reasoning.
Approach: Smart Curriculum Designer converts validated workflow artifacts into reusable learning modules.
Technical mechanism: Define the artifact packaging, provenance, validation, and generation pipeline.
Case study: Show a concrete AI/HPC workflow and the modules generated from it.
Scope statement: Say explicitly that this demonstrates a technical research-to-education mechanism, not improved student learning.
Draft wording to adapt
 
AI and high-performance computing workflows generate predictions, evaluation metrics, representative failures, resource traces, and provenance records that are central to how computational research is interpreted and reproduced. However, these execution artifacts are rarely available to students and new contributors as structured learning resources. We present Smart Curriculum Designer, a research-to-education pipeline that transforms validated AI/HPC workflow artifacts into role-specific instructional modules. The system packages workflow outputs using a provenance-aware artifact contract and generates walkthroughs, coding exercises, instructor materials, and low-risk contribution tasks grounded in those artifacts. We demonstrate the approach using a computer-vision workflow that produces cross-validation metrics, prediction records, model failures, segmentation outputs, explainability visualizations, and GPU telemetry. The contribution is a reusable mechanism for making operational workflow evidence inspectable and teachable; it does not claim improved learner outcomes. We discuss artifact validation, instructor control, and limitations for use in AI/HPC education.
 
 
 
Your paper should make clear that it is about research-to-education integration:
AI/HPC workflows generate evidence.
That evidence is normally difficult for students, educators, and new contributors to access and interpret.
The system packages selected evidence into instructional modules.
The modules teach not only AI concepts, but also workflow evaluation, reproducibility, resource awareness, and responsible interpretation.
This is much better aligned with EduHiPC’s Research-to-Education direction, which welcomes accounts of integrating research tools, models, simulations, datasets, and infrastructure into educational settings
 
Your introduction should have four short parts.
Paragraph 1: Explain the real educational problem
Explain that modern AI and HPC workflows are not just models. They include:
Data preparation.
Training and inference.
Cross-validation.
Resource allocation.
Runtime and memory behavior.
Failure analysis.
Provenance and reproducibility.
Validation and testing.
Documentation and contribution processes.
Students are often taught individual techniques but not how those components work together in a real computational workflow.
Paragraph 2: Explain why existing instructional resources are insufficient
Do not claim that all existing educational materials are inadequate. Say something more precise:
Conventional tutorials and static examples can teach isolated concepts, but they often do not expose the run-specific evidence that researchers use to interpret workflow behavior, investigate failures, assess resources, and reproduce results.
 
This is a defensible motivation.
Paragraph 3: Introduce the key insight
Use a clear transition:
Our premise is that validated workflow artifacts can serve as the bridge between research execution and education. A confusion matrix, a high-confidence error, a GPU memory trace, a segmentation mask, or a provenance record is not only a research byproduct; it can become the object of a learner’s analysis.
 
This should be the paper’s most memorable paragraph.
Paragraph 4: State contributions clearly
Use a concrete contribution list.
This paper makes the following contributions:
We define an artifact-to-learning-module contract that represents validated AI/HPC workflow outputs—including predictions, evaluation metrics, error cases, telemetry, visualizations, and provenance records—as structured inputs to instructional-material generation.
We implement Smart Curriculum Designer, a configurable pipeline that produces walkthroughs, coding exercises, instructor materials, and contribution-oriented tasks from those artifacts.
We demonstrate the approach using a computer-vision workflow and show how workflow-specific artifacts become modules on model evaluation, error analysis, segmentation, explainability, and resource-aware execution.
We document validation and instructor-review requirements for responsible use of LLM-assisted generation in research-to-education settings.
 
Do not include a contribution about “improved learning,” “reduced educator burden,” “accessibility,” “authentic learning,” or “greater flexibility” unless you have a matched evaluation for that outcome.
 
Include one end-to-end module
This is non-negotiable for credibility. The paper needs one compact but complete module trace:
Workflow output

Show a small prediction/evaluation/telemetry record—not an illustrative record that is disconnected from the actual run.
Provenance

Include run ID, data version, model version, fold/stage, and configuration identifier.
Selection logic

State exactly why the example was selected. For example: “highest-confidence false negative in fold 3,” or “slowest cross-validation fold with valid completed telemetry.”
Learning objective

Example: “Compute class-specific recall and explain why a high-confidence false negative can still occur.”
Student task

Give 3–4 concrete instructions.
Generated exercise

Include a compact code fragment with blanks or prompts.
Automated validation

Demonstrate that the expected output is obtained in a clean environment and matches the source artifact.
Instructor-facing interpretation

Include an answer or caveat—for example, that the error analysis does not establish clinical reliability or causality.
 
At present, HPC is mostly hidden in the implementation: Tapis, GPUs, vLLM, training throughput, and memory. That is not enough for EduHiPC.
You need at least one learner-facing module where HPC/PDC concepts are the learning target.
Add a module on workflow performance and parallelism
For example:
Module title: Understanding Parallel Cross-Validation on GPU Resources
Audience: Undergraduate AI/HPC students
Artifacts: Five-fold metric records, job timings, GPU-memory logs, throughput measurements, fold-to-worker mapping
Learning objective: Explain how independent cross-validation folds can be executed in parallel, and interpret the resulting performance and resource-use trade-offs
Student task: Compare per-fold runtimes and performance; identify whether one fold is slower; discuss whether throughput and memory results suggest a bottleneck; connect observed variation to model-evaluation practice
Output: A short notebook, data table, and instructor solution
Validation: All numerical values are read from the workflow-generated telemetry and metrics files
 
This module changes the paper from “we used HPC to generate content” to “we use workflow evidence to teach HPC reasoning.”
 
Include an explicit mapping table like
 
 
Learning module	AI/ML concept	HPC/PDC concept	Workflow artifacts used
Reading a model run	Classification workflow	Workflow orchestration	Run metadata and configuration
Cross-validation analysis	Evaluation and variance	Task parallelism	Per-fold results and timing
Error-analysis exercise	Misclassification and uncertainty	Data movement/reproducibility context	Prediction records and provenance
Segmentation exercise	Computer vision and IoU	Accelerated inference pipeline	Masks, runtime, and GPU data
Resource-aware AI exercise	Throughput and memory	GPU utilization/resource trade-offs	Peak memory and throughput traces
Reproducible contribution task	Testing and validation	Workflow reproducibility	Tests, logs, documentation, provenance
 
 
Remove unsupported template-versus-LLM claims
Right now, the paper says that templates limited flexibility and the LLM-driven version addressed this issue. That is plausible, but it is not demonstrated.
You have two choices.
Option A: Run a fair comparison
Use the same artifacts, objectives, audience, and module types for both systems.
Compare:
Template-based artifact injection.
LLM-based artifact-grounded generation.
Evaluate:
Coverage of learning objectives.
Technical correctness.
Artifact fidelity.
Domain specificity.
Consistency.
Number of developer edits required.
Number of educator edits required.
Ability to support a new module or domain.
Option B: Soften the section
If you cannot run the comparison, replace causal language with design rationale:
The template-based prototype provided predictable output structures but required manual authoring to expand the set of supported topics and activity types. We adopted LLM-based generation to explore a more configurable alternative. This paper does not evaluate whether the LLM-based approach improves instructional quality, educator workload, or learner outcomes relative to templates.
 
This is honest and academically stronger than an unsupported claim.
 
Do not claim domain independence from one skin-cancer workflow
 
Use a substantially different workflow, ideally one already available in the lab or ICICLE ecosystem:
Plant disease classification.
Crop or weed image classification.
Wildlife camera-trap classification.
Remote-sensing/geospatial classification.
Environmental sensor anomaly detection.
Scientific workflow-performance data.
Another reproducible AI/CI workflow with provenance records.
Keep the same artifact contract and generator code. Document only configuration changes.
 
Add a cross domain table like
 
 
Domain	Workflow type	Artifact bundle	Generator code changes	Configuration changes	Modules produced	Validation status
Skin lesions	Image classification	Predictions, metrics, errors, masks, telemetry	None	Dataset and learning goals	Evaluation, error analysis, segmentation, resource-awareness	Report results
Agriculture or ecology	Image classification or sensing workflow	Same common artifact types where applicable	None	Dataset and learning goals	Equivalent module types	Report results
 
 
Remember - We are not claiming that an LLM automatically solves curriculum design. We show how validated evidence from AI/HPC research workflows can be transformed into traceable, reusable learning modules that teach learners how to interpret, validate, reproduce, and contribute to those workflows.
 