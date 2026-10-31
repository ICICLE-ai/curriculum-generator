#!/bin/bash
set -e

CONFIG_FILE="${1:-sample_config.yaml}"

# 0. Enforce container-internal standard GCC compilers (prevents host HPC Spack leakage)
export CC=gcc
export CXX=g++
export NVCC_CCBIN=gcc

# 0b. Safeguard cache directories against host quota & stale cross-node P2P topology cache
export TRITON_CACHE_DIR="${TRITON_CACHE_DIR:-/tmp/triton_${SLURM_JOB_ID:-$$}}"
export TORCH_EXTENSIONS_DIR="${TORCH_EXTENSIONS_DIR:-/tmp/torch_extensions_${SLURM_JOB_ID:-$$}}"
mkdir -p "$TRITON_CACHE_DIR" "$TORCH_EXTENSIONS_DIR" 2>/dev/null || true

# 1. Parse LLM settings from YAML config
USE_LLM=$(python -c "import yaml; cfg=yaml.safe_load(open('${CONFIG_FILE}')); print(cfg.get('execution', {}).get('use_llm', False))" 2>/dev/null || echo "False")

# ==============================================================================
# STAGE 1: Execute Phase 1 Computer Vision Pipeline (100% GPU VRAM)
# ==============================================================================
echo "=================================================="
echo "STAGE 1: Executing Phase 1 Vision DL Pipeline..."
echo "=================================================="
python /app/run_pipeline.py "${CONFIG_FILE}" --phase 1

echo "[SUCCESS] Phase 1 Vision Pipeline completed. GPU memory fully released."

# ==============================================================================
# STAGE 2: Phase 2 Multi-Agent LLM Curriculum Generation (NRP managed LLM API;
# key from the NRP_LLM_API env var, sent per job by the web app)
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
