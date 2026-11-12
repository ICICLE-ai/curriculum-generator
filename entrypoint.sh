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
