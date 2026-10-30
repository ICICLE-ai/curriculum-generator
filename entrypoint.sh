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
export VLLM_CACHE_ROOT="/tmp/vllm_${SLURM_JOB_ID:-$$}"
export VLLM_NO_USAGE_STATS="${VLLM_NO_USAGE_STATS:-1}"
mkdir -p "$TRITON_CACHE_DIR" "$TORCH_EXTENSIONS_DIR" "$VLLM_CACHE_ROOT" 2>/dev/null || true

# 1. Parse LLM settings from YAML config
USE_LLM=$(python -c "import yaml; cfg=yaml.safe_load(open('${CONFIG_FILE}')); print(cfg.get('execution', {}).get('use_llm', False))" 2>/dev/null || echo "False")
LLM_MODEL=$(python -c "import yaml; cfg=yaml.safe_load(open('${CONFIG_FILE}')); print(cfg.get('execution', {}).get('llm_model') or 'Qwen/Qwen2.5-Coder-32B-Instruct')" 2>/dev/null || echo "Qwen/Qwen2.5-Coder-32B-Instruct")
LLM_BASE_URL=$(python -c "import yaml; cfg=yaml.safe_load(open('${CONFIG_FILE}')); print(cfg.get('execution', {}).get('llm_base_url') or 'http://localhost:8000/v1')" 2>/dev/null || echo "http://localhost:8000/v1")
LLM_DTYPE=$(python -c "import yaml; cfg=yaml.safe_load(open('${CONFIG_FILE}')); print(cfg.get('execution', {}).get('llm_dtype') or 'half')" 2>/dev/null || echo "half")
# Quantized checkpoints (e.g. GPTQ, which V100s support; AWQ needs compute capability >= 7.5)
LLM_QUANTIZATION=$(python -c "import yaml; cfg=yaml.safe_load(open('${CONFIG_FILE}')); print(cfg.get('execution', {}).get('llm_quantization') or '')" 2>/dev/null || echo "")
QUANT_ARGS=""
if [ -n "$LLM_QUANTIZATION" ]; then
    QUANT_ARGS="--quantization ${LLM_QUANTIZATION}"
fi
# 64k context: Qwen2.5 is trained to 32k, so YaRN rope scaling (factor 2) extends it.
# The KV cache on 2x V100 32GB with the 32B GPTQ model holds ~123k tokens (vLLM: 3.76x concurrency at 32k).
# Above 32k vLLM turns on chunked prefill, whose Triton kernel is Ampere-only and kills the engine on V100s.
CONTEXT_ARGS="--max-model-len 65536 --rope-scaling {\"rope_type\":\"yarn\",\"factor\":2.0,\"original_max_position_embeddings\":32768} --enable-chunked-prefill=False"

# ==============================================================================
# STAGE 1: Execute Phase 1 Computer Vision Pipeline (100% GPU VRAM)
# ==============================================================================
echo "=================================================="
echo "STAGE 1: Executing Phase 1 Vision DL Pipeline..."
echo "=================================================="
python /app/run_pipeline.py "${CONFIG_FILE}" --phase 1

echo "[SUCCESS] Phase 1 Vision Pipeline completed. GPU memory fully released."

# ==============================================================================
# STAGE 2: Start vLLM & Execute Phase 2 Multi-Agent LLM Curriculum Generation
# ==============================================================================
if [ "$USE_LLM" = "True" ] || [ "$USE_LLM" = "true" ]; then
    echo "=================================================="
    echo "STAGE 2: Starting vLLM & Phase 2 Multi-Agent LLM..."
    echo "=================================================="

    if [[ "$LLM_BASE_URL" == *"localhost:8000"* ]] || [[ "$LLM_BASE_URL" == *"127.0.0.1:8000"* ]]; then
        if ! python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/v1/models', timeout=2)" > /dev/null 2>&1; then
            # Detect available GPUs for automatic Tensor Parallelism
            NUM_GPUS=$(python -c "import torch; print(torch.cuda.device_count())" 2>/dev/null || echo 1)
            if [ -z "$NUM_GPUS" ] || [ "$NUM_GPUS" -lt 1 ]; then
                NUM_GPUS=1
            fi
            echo "[INFO] Detected ${NUM_GPUS} GPU(s) available for vLLM."

            TP_ARGS=""
            if [ "$NUM_GPUS" -gt 1 ]; then
                echo "[INFO] Enabling Tensor Parallelism across ${NUM_GPUS} GPUs (--tensor-parallel-size ${NUM_GPUS} --disable-custom-all-reduce)."
                TP_ARGS="--tensor-parallel-size ${NUM_GPUS} --disable-custom-all-reduce"
            fi

            echo "[INFO] Starting local vLLM server for '${LLM_MODEL}' on port 8000..."
            if command -v vllm >/dev/null 2>&1; then
                vllm serve "${LLM_MODEL}" --port 8000 --gpu-memory-utilization 0.90 ${CONTEXT_ARGS} --dtype "${LLM_DTYPE}" ${QUANT_ARGS} ${TP_ARGS} &
            else
                python -m vllm.entrypoints.openai.api_server --model "${LLM_MODEL}" --port 8000 --gpu-memory-utilization 0.90 ${CONTEXT_ARGS} --dtype "${LLM_DTYPE}" ${QUANT_ARGS} ${TP_ARGS} &
            fi
            VLLM_PID=$!
            
            # Ensure background process is killed when container/script exits
            trap 'echo "[INFO] Cleaning up vLLM process..."; kill $VLLM_PID 2>/dev/null || true' EXIT

            echo "[INFO] Waiting for vLLM endpoint on port 8000 (PID: $VLLM_PID)..."
            MAX_WAIT_SECONDS=1500
            ELAPSED=0
            until python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/v1/models', timeout=2)" > /dev/null 2>&1; do
                if ! kill -0 $VLLM_PID 2>/dev/null; then
                    echo "[ERROR] vLLM server process ($VLLM_PID) exited or failed to start."
                    exit 1
                fi
                if [ $ELAPSED -ge $MAX_WAIT_SECONDS ]; then
                    echo "[ERROR] Timed out after ${MAX_WAIT_SECONDS}s waiting for vLLM server to start."
                    exit 1
                fi
                sleep 5
                ELAPSED=$((ELAPSED + 5))
            done
            echo "[SUCCESS] vLLM server is ready!"
        else
            echo "[INFO] vLLM server already active on port 8000."
        fi
    fi

    # Execute Phase 2 Multi-Agent LLM Synthesis & Presentation Decks
    echo "[INFO] Executing Phase 2 Multi-Agent LLM Curriculum Synthesis..."
    python /app/run_pipeline.py "${CONFIG_FILE}" --phase 2
fi

echo "=================================================="
echo "All Pipeline Stages Completed Successfully!"
echo "=================================================="

