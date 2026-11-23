#!/bin/bash
set -e

CONFIG_FILE="${1:-sample_config.yaml}"

# 0. Enforce container-internal standard GCC compilers (prevents host HPC Spack leakage)
export CC=gcc
export CXX=g++
export NVCC_CCBIN=gcc
# Batch stdout is a file, so Python block-buffers it: Phase 2 progress reached tapisjob.out hours late
export PYTHONUNBUFFERED=1

# 0b. Safeguard cache directories against host quota & stale cross-node P2P topology cache
export TRITON_CACHE_DIR="${TRITON_CACHE_DIR:-/tmp/triton_${SLURM_JOB_ID:-$$}}"
export TORCH_EXTENSIONS_DIR="${TORCH_EXTENSIONS_DIR:-/tmp/torch_extensions_${SLURM_JOB_ID:-$$}}"
mkdir -p "$TRITON_CACHE_DIR" "$TORCH_EXTENSIONS_DIR" 2>/dev/null || true

# 1. Parse LLM settings from YAML config
USE_LLM=$(python -c "import yaml; cfg=yaml.safe_load(open('${CONFIG_FILE}')); print(cfg.get('execution', {}).get('use_llm', False))" 2>/dev/null || echo "False")

# Fail before Phase 1 trains anything if Phase 2 will have no LLM credential: the Tapis refresh token the web app
# sends (for the project's LLM proxy), or NRP_LLM_API for configs that call NRP directly
if { [ "$USE_LLM" = "True" ] || [ "$USE_LLM" = "true" ]; } && [ -z "${TAPIS_REFRESH_TOKEN// /}${NRP_LLM_API// /}" ]; then
    echo "[ERROR] use_llm is true but the job has no TAPIS_REFRESH_TOKEN. Submit the job from the web app."
    exit 1
fi

# 1b. Tapis writes the job's environment, secrets included, into tapisjob.env and into the singularity command of
# tapisjob.sh in the job folder, which every user of the shared expanse-tapis-static account can read. This process
# already has them, so blank them on disk. Each file is replaced, not edited, so the batch shell still running
# tapisjob.sh keeps reading the original it has open.
for job_file in tapisjob.sh tapisjob.env; do
    if [ -f "$job_file" ]; then
        sed -E 's/(TAPIS_REFRESH_TOKEN|NRP_LLM_API)=("[^"]*"|[^ ,"]*)/\1="<removed>"/g' "$job_file" > "$job_file.redacted" \
            && mv -f "$job_file.redacted" "$job_file" \
            && echo "[INFO] Removed credentials from $job_file"
    fi
done

# ==============================================================================
# Local vision-model slide review test (scripts/submit_phase2_rerun.py --task vlm_test): GPU queue, no pipeline;
# with --vlm-model none only the NRP reviewers run, on the CPU queue.
# Serves a small VLM with a pinned vLLM and compares its reviews with deepseek's (scripts/vlm_review_test/)
# ==============================================================================
if [ -n "${VLM_TEST// /}" ]; then
    bash /app/scripts/vlm_review_test/run.sh
    exit 0
fi

# ==============================================================================
# Pedagogy evaluation of a finished run (scripts/submit_phase2_rerun.py --task evaluate|damage): no pipeline, CPU
# queue. EVAL_FROM_DIR is that run's job directory; its Phase 1 outputs and finished weeks are copied here and scored
# into ./outputs/<run>/exercises/evaluation/. EVAL_ARGS are extra script flags, e.g. "--repeat 2 --weeks Week_01"
# ==============================================================================
if [ -n "${EVAL_FROM_DIR// /}" ]; then
    case "${EVAL_SCRIPT:=evaluate_curriculum}" in
        evaluate_curriculum|damage_test) ;;
        *) echo "[ERROR] EVAL_SCRIPT must be evaluate_curriculum or damage_test, got '${EVAL_SCRIPT}'"; exit 1 ;;
    esac
    echo "=================================================="
    echo "PEDAGOGY EVALUATION (${EVAL_SCRIPT}) of ${EVAL_FROM_DIR} ${EVAL_ARGS}"
    echo "=================================================="
    set -f  # EVAL_ARGS is split into words but never expanded as file globs
    python "/app/scripts/${EVAL_SCRIPT}.py" --config "${CONFIG_FILE}" --from-run "${EVAL_FROM_DIR}" ${EVAL_ARGS}
    exit 0
fi

# ==============================================================================
# Phase 2 rerun (set by the web app's "Run Phase 2 again"): no Phase 1, so it runs on the CPU queue. Phase 1's
# outputs are copied from the finished run's job directory; RERUN_WEEKS is "failed" (default) or "all"
# ==============================================================================
if [ -n "${RERUN_FROM_DIR// /}" ]; then
    echo "=================================================="
    echo "PHASE 2 RERUN from ${RERUN_FROM_DIR} (weeks: ${RERUN_WEEKS:-failed})"
    echo "=================================================="
    python /app/run_pipeline.py "${CONFIG_FILE}" --phase 2 --from-run "${RERUN_FROM_DIR}" --weeks "${RERUN_WEEKS:-failed}"
    echo "=================================================="
    echo "Phase 2 Rerun Completed Successfully!"
    echo "=================================================="
    exit 0
fi

# ==============================================================================
# STAGE 1: Execute Phase 1 Computer Vision Pipeline (100% GPU VRAM)
# ==============================================================================
echo "=================================================="
echo "STAGE 1: Executing Phase 1 Vision DL Pipeline..."
echo "=================================================="
python /app/run_pipeline.py "${CONFIG_FILE}" --phase 1

echo "[SUCCESS] Phase 1 Vision Pipeline completed. GPU memory fully released."

# ==============================================================================
# STAGE 2: Phase 2 Multi-Agent LLM Curriculum Generation (NRP managed LLM API, through the project's
# LLM proxy, which holds the NRP key; the job authenticates with the user's Tapis refresh token)
# ==============================================================================
if [ "$USE_LLM" = "True" ] || [ "$USE_LLM" = "true" ]; then
    echo "=================================================="
    echo "STAGE 2: Executing Phase 2 Multi-Agent LLM Curriculum Synthesis..."
    echo "=================================================="
    python /app/run_pipeline.py "${CONFIG_FILE}" --phase 2
fi

echo "=================================================="
echo "All Pipeline Stages Completed Successfully!"
echo "=================================================="
