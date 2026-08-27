# Sprint Four - Multi-Agent LLM Synthesis, Cloud RAG, Containerized HPC Serving & Educator Portal

## 08/08/2026

The primary goal today was to integrate the autonomous 3-Tier Multi-Agent LLM curriculum engine from the upstream research repository into DigitalAgEdu, establishing the Phase 2 pedagogical code and slide synthesizer.

| Component | What | Why |
| :--- | :--- | :--- |
| **Phase 2 LLM Architecture Integration** | Integrated `digitalagedu/core/llm/` containing `main.py`, `ai_setup.py`, `context.py`, `sandbox.py`, `slide_builder.py`, and `telemetry.py`. | Shifts curriculum generation from static Jinja2 template interpolation to an autonomous multi-agent pipeline capable of writing custom Python exercises, starter code, and solution keys. |
| **3-Tier Multi-Agent Pipeline** | Implemented sequential agent roles: Agent 0 (Problem Formulation), Agent 1 (PyTorch Reference Solution Builder), and Agent 2 (Adversarial Unit Testing & Verification). | Guarantees pedagogical rigor, step-by-step code scaffolding, and 100% executable student exercises without syntax or runtime bugs. |
| **Structured Output Schemas** | Authored typed Pydantic models in `digitalagedu/core/llm/schemas/` (`generation_types.py`, `module_types.py`). | Enforces strict JSON grammar decoding from the LLM, preventing malformed outputs and missing exercise fields. |
| **Multimodal Context Ingestion** | Implemented `build_pedagogical_context` in `digitalagedu/core/llm/context.py` to ingest Phase 1 CV artifacts (`results.csv`, SAM mask paths, Grad-CAM attention maps, and RAG knowledge vectors). | Grounds the LLM's reasoning and coding assignments directly in authentic computer vision experimental outputs. |
| **Marp Slide Deck Synthesizer** | Created `slide_builder.py` to generate presentation-ready Marp markdown slide decks for each weekly module. | Delivers ready-to-teach lecture slides with learning objectives, code walkthroughs, and architectural diagrams. |
| **Initial Chroma Vector Store** | Initialized local ChromaDB vector storage (`chroma_db/chroma.sqlite3`) storing domain-specific documentation chunks. | Provides foundational retrieval-augmented generation (RAG) capabilities to anchor agent prompts in domain literature. |

---

## 08/09/2026

The primary goal today was to enforce strict two-phase pipeline orchestration (Phase 1 CV $\rightarrow$ Phase 2 LLM), patch legacy SQLite3 dependencies on HPC compute nodes, and ensure robust offline telemetry fallbacks.

| Component | What | Why |
| :--- | :--- | :--- |
| **Two-Phase Execution Ordering** | Restructured `cluster_jobs/run_job_vllm.sh` to guarantee that Phase 1 Computer Vision feature extraction (DINOv2, SAM, Grad-CAM) executes and outputs all artifacts to disk before launching vLLM and Phase 2 LLM synthesis. | Prevents race conditions and ensures Agent 0 has access to complete model accuracy metrics, confusion tables, and image samples. |
| **SQLite3 Monkeypatch for ChromaDB** | Injected `pysqlite3-binary` override (`sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")`) inside `build_rag.py` and `context.py`. | Resolves critical `RuntimeError: Your system has an unsupported version of sqlite3` crashes caused by outdated system libraries on Linux HPC clusters. |
| **Non-Blocking W&B Offline Mode** | Updated `curriculum_resources/week_08/solution.py` to check for `WANDB_API_KEY` and gracefully default `WANDB_MODE=offline` when unauthenticated. | Prevents cluster batch jobs from aborting with network socket or authentication exceptions during automated Slurm runs. |

---

## 08/10/2026

The primary goal today was to decouple output directory paths, streamline CLI parameter handling, and establish system-agnostic container execution commands.

| Component | What | Why |
| :--- | :--- | :--- |
| **Optional Output Path Routing** | Updated `generate_llm_curriculum` in `digitalagedu/core/llm/main.py` to make `output_dir` optional, defaulting to `./exercises/` subfolders within the project output root. | Prevents path resolution errors when executing in headless container environments with custom output folder trees. |
| **Dataset Registry & CLI Cleanup** | Streamlined `digitalagedu/core/dataset_registry.py` and `digitalagedu/cli.py`, removing obsolete arguments and parameter errors. | Standardizes dataset discovery and command-line interfaces across both interactive and batch runs. |
| **System-Agnostic Container Entrypoint** | Refactored `app.json` and `entrypoint.sh` to support uniform execution across Docker, Apptainer, and Singularity container runtimes. | Guarantees portability across heterogeneous academic supercomputing clusters (OSC, TACC, Nautilus). |

---

## 08/13/2026

The primary goal today was to migrate vector storage from local ChromaDB to cloud Qdrant pods on ICICLE, author Tapis v3 application manifests, and publish comprehensive public documentation.

| Component | What | Why |
| :--- | :--- | :--- |
| **Cloud Qdrant Vector DB Migration** | Built `digitalagedu/core/llm/rag/qdrant_client.py` and migrated domain knowledge vectors to ICICLE Qdrant Pods (`https://digitalageduqdrant.pods.icicleai.tapis.io`). | Sacked 29MB local SQLite binaries (`chroma_db/`), eliminating filesystem locking conflicts on distributed cluster scratch drives. |
| **Qdrant Client Architecture** | Implemented asynchronous and synchronous Qdrant clients with 384-dimensional dense embeddings (`all-MiniLM-L6-v2`), payload filtering, batch upserts, and cosine similarity search. | Provides fast, scalable retrieval of domain science context and pedagogical guidelines for LLM agents. |
| **Migration & Diagnostic Scripts** | Created `scripts/migrate_rag_to_qdrant.py`, `scripts/test_live_qdrant.py`, `scripts/test_store_embedding.py`, and `scripts/verify_connection.py`. | Facilitates automated collection initialization, embedding generation, and cluster connectivity verification. |
| **Tapis v3 Application Manifest** | Created `app_testing.json` and updated `app.json` with Slurm scheduler bindings, dynamic `$TAPIS_JWT` injection, and container directory mounts. | Allows users to submit, monitor, and manage DigitalAgEdu curriculum generation jobs via the Tapis API ecosystem. |
| **Public Documentation Overhaul** | Authored `documentation/HOW_TO_USE.md` (complete user and cluster deployment guide) and `documentation/YAML_CONFIG_GUIDE.md` (exhaustive parameter specification). | Provides researchers and educators with clear, step-by-step instructions for configuring and running the pipeline. |
| **Sprint Logs Reorganization** | Moved historical developer logs into `documentation/dev/` (`sprint_one.md`, `sprint_two.md`, `sprint_three.md`, `sprint_four.md`). | Organizes internal engineering milestones into a dedicated developer archive. |

---

## 08/14/2026

The primary goal today was to automate the vLLM OpenAI-compatible server lifecycle within container startup scripts and integrate Outlines for deterministic structured grammar decoding.

| Component | What | Why |
| :--- | :--- | :--- |
| **Automated vLLM Background Serving** | Configured `entrypoint.sh` and `cluster_jobs/run_job_vllm.sh` to automatically launch `vllm serve Qwen/Qwen2.5-Coder-32B-Instruct-AWQ` in the background (`--port 8000`, `--gpu-memory-utilization 0.85`, `--max-model-len 8192`). | Eliminates manual server startup steps, allowing single-command execution of the entire vision-to-LLM pipeline inside cluster jobs. |
| **Outlines Grammar-Guided Decoding** | Added `outlines` dependency to `requirements.txt` and integrated grammar constraints into the agent client. | Guarantees that generated Python code snippets strictly conform to executable syntax and required function signatures. |
| **Hurricane Domain Configuration** | Authored `configs/hurricane_config.yaml` demonstrating satellite imagery categorization, cyclone tracking modules, and LLM lesson generation. | Validates the domain generality of the multi-agent system on earth and atmospheric science datasets. |

---

## 08/15/2026

The primary goal today was to upgrade container CUDA toolkits for modern GPU architectures, pin critical machine learning dependencies, and implement robust vLLM model loading timeouts.

| Component | What | Why |
| :--- | :--- | :--- |
| **CUDA 12.4 Docker Upgrade** | Updated `Dockerfile` base image to `nvidia/cuda:12.4.1-devel-ubuntu22.04` with Python 3.10 and PyTorch 2.4+CUDA 12.4 wheels. | Unlocks native support for NVIDIA Hopper (H100) and Blackwell GPU architectures while maintaining backward compatibility with A100/V100 nodes. |
| **Dependency Pinning & Conflicts Resolution** | Pinned `transformers<=4.44.2`, `vllm>=0.5.4`, `pydantic>=2.0`, `pyairports`, and `pycountry` in `requirements.txt`. | Resolves upstream library breaking changes, Pydantic v2 serialization conflicts, and HuggingFace tokenization mismatches. |
| **vLLM Startup Polling Extension** | Extended the container startup polling timeout loop in `entrypoint.sh` from 60s to 300s. | Prevents premature job termination while large 32B AWQ quantized model weights are decompressed and loaded into GPU memory. |

---

## 08/16/2026

The primary goal today was to resolve container line-ending execution aborts, design the HPC Reverse Port-Forwarding architecture, construct a modern Vite/React educator portal with Tapis Token Management and Dynamic YAML Building, and author a pedagogy-first Knowledge Bank.

| Component | What | Why |
| :--- | :--- | :--- |
| **Native Python Socket Healthcheck** | Replaced `curl` in `entrypoint.sh` with a native Python socket script (`urllib.request.urlopen('http://localhost:8000/v1/models')`). | Resolves `curl: not found` execution crashes on minimal Docker/Apptainer container base images. |
| **CRLF to LF Line Ending Normalization** | Converted `entrypoint.sh` and shell scripts from Windows CRLF to Unix LF line endings. | Fixes bash syntax aborts (`$'\r': command not found`) when executing Windows-edited container files on Linux nodes. |
| **HPC Reverse Port-Forwarding Architecture** | Authored `tasks/HPC_REVERSE_TUNNEL_VITE_UI_PLAN.md` detailing reverse SSH tunneling (`ssh -R 8000:localhost:8000`) and TLS gateway integration. | Enables secure, zero-cloud-dependency remote browser interaction between local educator laptops and private cluster compute nodes. |
| **Tapis Token Manager & Live JWT Decoder** | Built `frontend/src/components/TokenManager.tsx` supporting direct token pasting and OAuth token generation via `/v3/tokens` POST/PUT on ICICLE AI (`https://icicleai.tapis.io`). | Features client-side base64 JWT decoding, live expiration countdown timers, preset TTL selectors, and a compact 2-column no-scroll layout. |
| **Dynamic YAML Curriculum Builder** | Built `frontend/src/pages/ConfigPage.tsx` matching `skin_cancer_config.yaml` schema with dynamic `+ Add Module` and `+ Add Resource` managers. | Enables educators to build custom multi-week syllabi with custom titles, week numbers, difficulty ratings, and external learning links without editing raw YAML code. |
| **Removal of Standalone VisionQA Stage** | Sacked standalone Phi-3-Vision stage from the pipeline, injecting visual reasoning directly into the Phase 2 LLM multi-agents. | Simplifies the vision pipeline to DINOv2 classification $\rightarrow$ SAM segmentation $\rightarrow$ Grad-CAM XAI while lowering GPU VRAM footprint. |
| **Admin Settings Abstraction** | Hidden W&B telemetry and Qdrant cloud connection strings from the educator form and YAML preview. | Keeps generated YAML files clean and prevents non-technical teachers from having to manage infrastructure connection strings. |
| **Pedagogy-First Knowledge Bank & Help Modals** | Created `frontend/src/data/configFieldGuide.ts` and `frontend/src/components/FieldHelpModal.tsx` mapping all fields to plain-English classroom benefits. | Replaces dense ML jargon with intuitive explanations of how each parameter enhances student slides, coding exercises, and learning outcomes. |
| **Global UI & Typography Modernization** | Implemented transparent scrollbars, dark glassmorphism theme, Inter/JetBrains Mono typography, and strict emoji-free styling across all views. | Delivers a responsive, professional, and accessible user experience across all screen sizes. |
| **RAG Cloud Import Cleanup** | Removed obsolete `build_rag.py` / `scripts.migrate_rag_to_qdrant` imports from `digitalagedu/core/llm/__init__.py`. | Fixes `ModuleNotFoundError` during Phase 2 initialization by relying entirely on live cloud Qdrant querying (`query_similar`). |
| **Sequential Vision $\rightarrow$ LLM Lifecycle** | Implemented `--phase` CLI flag (`1`, `2`, `all`) in `run_pipeline.py` and refactored `entrypoint.sh` into sequential stages. | Gives Phase 1 (DINOv2 + SAM) 100% of GPU VRAM, releases memory upon completion, and then launches vLLM with full memory allocation for Phase 2 without OOM crashes. |
| **Weekly Multi-Agent Output Hierarchy** | Restructured `digitalagedu/core/llm/main.py` to organize all generated overviews, slide decks (`.pptx`), starter codes, solutions, and unit tests into `output/exercises/Week_XX/{module_id}/`. | Provides clean, student-ready weekly lab directories matching pedagogical course progression. |
| **Legacy Template Generation Retirement** | Sacked `PracticeGenerator` and the legacy Jinja2 template matching loop from `run_pipeline.py`. | Transitions the entire exercise synthesis pipeline to autonomous, verified 3-Tier Multi-Agents. |
| **Production Frontend Deployment on Tapis Pods** | Provisioned standalone Nginx Tapis Pod `digitalagedu` (`https://digitalagedu.pods.icicleai.tapis.io`) backed by `digitalagedustorage` volume. | Hosts the complete React/Vite educator portal 24/7 on ICICLE cloud with automated SSL and persistent storage. |
| **Automated Pod Asset Synchronization** | Built `upload_frontend.py` using Tapis Pods upload APIs to push production `dist/` HTML, JavaScript, CSS, and SVG assets into `/usr/share/nginx/html/`. | Automates zero-downtime frontend releases directly from local development builds to the live cloud pod. |

---

## 08/17/2026

The primary goal today was to build robust chunked asset synchronization for Tapis Pods, implement live Tapis job telemetry monitoring, and add token refresh management into the educator portal.

| Component | What | Why |
| :--- | :--- | :--- |
| **Chunked Base64 Tapis Pod Asset Sync** | Built `scripts/sync_frontend_to_pod.py` streaming `frontend/dist/` production assets in 40KB base64 chunks via `exec_pod_commands` to `/usr/share/nginx/html/` with proper `644`/`755` permissions. | Bypasses Tapis Pod API upload size limitations and eliminates upload timeouts when deploying frontend bundles. |
| **Live Pipeline & Job Monitor UI** | Created real-time telemetry dashboard in `frontend/src/pages/MonitorPage.tsx` integrating `/v3/jobs/list`, tracking execution system, node/core allocations, elapsed runtime, and stage progress bars. | Gives educators direct visibility into remote HPC cluster execution progress and diagnostic telemetry. |
| **User Token Session & Refresh Management** | Built `frontend/src/components/UserTokenDropdown.tsx` featuring persistent user authentication state, token TTL countdown timers, quick renewal via `POST /v3/tokens`, and logout actions. | Prevents session expiration disruptions while educators configure curricula and monitor jobs. |
| **Tapis Job Output File Extraction** | Implemented `fetchJobProgress`, `fetchJobLogs`, and `listJobOutputFiles` in `frontend/src/utils/tapisJobs.ts` using `/v3/files/ops` and `/v3/files/content`. | Enables direct dynamic extraction of `progress.json` telemetry and raw execution logs from HPC scratch directories. |

---

## 08/18/2026

The primary goal today was to complete the elimination of legacy template systems, refactor syllabus rendering to standalone Jinja2 templates, clean up resource directories, and author core unit tests.

| Component | What | Why |
| :--- | :--- | :--- |
| **Total Elimination of Legacy Template Generators** | Deleted `digitalagedu/core/practice_generator.py`, `digitalagedu/core/concepts_registry.py`, and `digitalagedu/core/scanner.py`. | Eliminates dead legacy template code, shifting 100% of curriculum creation to autonomous LLM multi-agents. |
| **Standalone Jinja2 Syllabus Template** | Isolated the lesson plan template into `digitalagedu/templates/lesson_plan.md.j2` and refactored `TemplateRenderer` to use `FileSystemLoader`. | Maintains clean separation between pedagogical rendering logic and markdown templates. |
| **Resource Folder Reorganization** | Removed obsolete `curriculum_resources/week_11` and renamed `curriculum_resources/week_08` $\rightarrow$ `classification` and `curriculum_resources/week_09` $\rightarrow$ `segmentation`. | Cleans up codebase naming conventions to represent computer vision domains rather than hardcoded week indices. |
| **Pipeline Stage Module Routing Update** | Updated dynamic module imports in `digitalagedu/core/config.py`, `curriculum_resources/xai/solution.py`, `configs/food_config.yaml`, and `configs/hurricane_config.yaml`. | Ensures all vision pipeline stages route seamlessly to the new module paths. |
| **Core Engine Test Suite** | Created `tests/test_curriculum_engine.py` verifying clean imports, `CurriculumService`, `TemplateRenderer`, and prompt builders. | Provides automated test coverage for core configuration parsing and curriculum rendering. |

---

## 08/19/2026

The primary goal today was to resolve production Tapis Pods API routing errors, research AI presentation tools, and integrate headless in-job Presenton AI presentation generation with deep domain context and zero fallback.

| Component | What | Why |
| :--- | :--- | :--- |
| **Tapis Pods NGINX 404 Resolution** | Updated `getTapisApiUrl` in `frontend/src/utils/tapisJobs.ts` to detect production hosting on Tapis Pods and route API calls to `https://icicleai.tapis.io`. | Resolves NGINX `404 Not Found` when fetching user jobs on `digitalagedu.pods.icicleai.tapis.io`. |
| **Presenton AI Presentation Research & Plan** | Researched Presenton Docker/FastAPI architecture and authored `tasks/PRESENTON_HEADLESS_PPTX_INTEGRATION_PLAN.md` detailing headless synchronous REST generation. | Establishes the technical foundation for template-free, dynamic AI slide generation. |
| **Headless Synchronous Presenton Client** | Built `digitalagedu/core/llm/presenton_client.py` targeting `POST /api/v1/ppt/presentation/generate` to synchronously one-shot compile `.pptx` decks and stream binary bytes to disk. | Enables 100% headless, programmatic presentation synthesis with zero browser or UI dependency. |
| **Deep Domain-to-Concept Context Grounding** | Created `build_presenton_payload` in `digitalagedu/core/llm/context.py` assembling rich domain problem directives (Agent 0), Phase 1 telemetry (classes, dataset size, baseline accuracy, contrastive success/failure cases), Agent 1 PyTorch architecture code, and structured `slides_markdown`. | Bridges authentic domain science challenges directly to machine learning theory and implementation. |
| **Multi-Agent Orchestration Update** | Reorganized lifecycle (Agent 0 $\rightarrow$ Agent 1 $\rightarrow$ Agent 2 $\rightarrow$ Presenton Presentation) in `digitalagedu/core/llm/main.py` and deleted legacy rigid `slide_builder.py` with no template fallback. | Delivers fully AI-composed, visually dynamic slide decks for each weekly module. |
| **Single-Container In-Job Daemon Co-Location** | Updated `entrypoint.sh` to launch the local Presenton daemon on port 5001 alongside `vLLM` on port 8000 during Stage 2 with automatic termination traps. | Ensures full compliance with ICICLE container allow-lists without spawning external pods. |
| **Presenton Integration Test Suite** | Authored `tests/test_presenton_integration.py` covering client health check, deep domain payload validation, and synchronous `.pptx` generation and error handling. | Guarantees test verification for the Presenton client and context builder. |

---

## 08/20/2026

The primary goal today was to analyze HPC execution telemetry logs (`tapisjob.out`), identify Phase 2 LLM generation bottlenecks, and scale token context limits across the multi-agent synthesis pipeline.

| Component | What | Why |
| :--- | :--- | :--- |
| **Telemetry Log Diagnostic Analysis** | Analyzed `tapisjob.out` from cluster execution, confirming 100% success on Phase 1 CV pipelines (3,297 images, 88.11% accuracy, SAM segmentation) and identifying Agent 0 truncation. | Isolates the exact failure boundary where Agent 0 hit token exhaustion on large markdown overviews. |
| **Agent Generation Token Limit Scaling** | Scaled `max_tokens` across the multi-agent pipeline: Agent 0 (`2500` $\rightarrow$ `8192`), Agent 1 (`4096` $\rightarrow$ `8192`), and Agent 2 (`1500` $\rightarrow$ `4096`). | Leverages the 57.45 GiB KV cache in vLLM to allow comprehensive, multi-page Markdown tutorials, full PyTorch architectures, and property-based test suites without mid-generation truncation. |

---

## 08/21/2026

The primary goal today was to resolve sandbox unit test import resolution for module-named solution files, diagnose Presenton FastAPI daemon startup requirements, and package backend wheel dependencies into the container build.

| Component | What | Why |
| :--- | :--- | :--- |
| **Sandbox Multi-Module Alias Resolution** | Updated `digitalagedu/core/llm/sandbox.py` to create both `solution.py`, `[module_id]_solution.py`, and regex-matched `*_solution.py` file aliases in the isolated temp directory. | Prevents `ModuleNotFoundError: No module named 'numpy_basics_solution'` when Agent 2 imports named module files in the test runner. |
| **Presenton Backend Wheel Packaging** | Configured `Dockerfile` to install `/app/presenton/servers/fastapi/dist/*.whl` and updated `entrypoint.sh` to target `api.main:app` with `--app-dir /app/presenton/servers/fastapi`. | Installs required dependencies (`fastapi_users`, `alembic`, `fastembed`) so the Presenton slide daemon boots cleanly on port 5001. |
| **Autograd Hook Signature Rule Enforcement** | Updated hook contract rule 9 in `digitalagedu/core/llm/context.py` to explicitly enforce `(self, module, grad_in, grad_out)`. | Eliminates `TypeError: activations_hook takes 3 positional arguments but 4 were given` in synthesized PyTorch feature attribution code. |

---

## 08/23/2026

The primary goal today was to diagnose the Presenton template asset file permissions on HPC rootless execution and verify multi-agent pipeline stages from cluster telemetry logs.

| Component | What | Why |
| :--- | :--- | :--- |
| **Presenton Asset Permissions Fix** | Added `RUN chmod -R a+rX /app/presenton` to `Dockerfile` and configured `APP_DATA_DIRECTORY=/tmp/presenton_data` in `entrypoint.sh`. | Resolves `shutil.Error: [Errno 13] Permission denied` when Presenton copies fonts/SVGs to `/tmp/presenton_data/templates` in rootless Apptainer execution. |
| **Presenton Headless Auth Bypass & Self-Healing** | Set `DISABLE_AUTH=true` in `entrypoint.sh` and added a self-healing retry hook in `PresentonClient` for `428 Precondition Required`. | Resolves `{"detail":"Login setup is required"}` error so headless batch slide generation executes without login setup roadblocks. |

---

## 08/24/2026

The primary goal today was to diagnose Presenton admin credential persistence during container startup and configure `USER_CONFIG_PATH`.

| Component | What | Why |
| :--- | :--- | :--- |
| **Presenton Config Path Export** | Added `export USER_CONFIG_PATH="/tmp/presenton_data/userConfig.json"` to `entrypoint.sh`. | Resolves `ValueError: USER_CONFIG_PATH is not set` in `api/v1/auth/config.py` during `bootstrap_database_admin()` execution. |

---

## 08/26/2026

The primary goal today was to scale the Presenton client read timeout to accommodate full 12-slide multi-agent PowerPoint generation and schema validation.

| Component | What | Why |
| :--- | :--- | :--- |
| **Presenton Client Timeout Scaling** | Increased `DEFAULT_PRESENTON_TIMEOUT` from `180.0s` (3 min) to `600.0s` (10 min) in `digitalagedu/core/llm/presenton_client.py` with environment variable override (`PRESENTON_TIMEOUT`). | Prevents client-side HTTP `Read timed out` while Presenton and vLLM synthesize, validate, and compile full 12-slide presentation decks. |

---

## 08/27/2026

The primary goal today was to install headless Chromium and Puppeteer export rendering dependencies to enable Presenton's full AI-driven dynamic visual presentation compilation and `.pptx` export.

| Component | What | Why |
| :--- | :--- | :--- |
| **Chromium & Puppeteer System Runtime** | Installed Google Chrome (`google-chrome-stable` direct `.deb`), Node.js 20 from NodeSource, and font libraries in `Dockerfile`, and exported `PUPPETEER_EXECUTABLE_PATH=/usr/bin/google-chrome-stable` in `Dockerfile` and `entrypoint.sh`. | Resolves Ubuntu Snap conflicts (`exit code 100`) and missing browser binaries (`[Errno 2] No such file or directory`) during Presenton's `export_from_url` task. |
| **Presenton Schema `anyOf` Sanitizer** | Implemented `scripts/patch_presenton_schemas.py` and hooked it into Presenton's `llm_utils.py` and Docker build. Converts any schema `"type": ["string", "null"]` list unions into standard `"anyOf": [{"type": "string"}, {"type": "null"}]`. | Resolves vLLM `outlines` regex compiler failure (`ValueError: 'type' must be a string`), allowing diverse slide layouts (like `title_description_chart_cards`) to generate without 400 Bad Request errors. |










