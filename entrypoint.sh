#!/bin/bash
set -e

CONFIG_FILE="${1:-sample_config.yaml}"

# 1. Parse LLM settings from YAML config
USE_LLM=$(python -c "import yaml; cfg=yaml.safe_load(open('${CONFIG_FILE}')); print(cfg.get('execution', {}).get('use_llm', False))" 2>/dev/null || echo "False")
LLM_MODEL=$(python -c "import yaml; cfg=yaml.safe_load(open('${CONFIG_FILE}')); print(cfg.get('execution', {}).get('llm_model') or 'Qwen/Qwen2.5-Coder-32B-Instruct-AWQ')" 2>/dev/null || echo "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ")
LLM_BASE_URL=$(python -c "import yaml; cfg=yaml.safe_load(open('${CONFIG_FILE}')); print(cfg.get('execution', {}).get('llm_base_url') or 'http://localhost:8000/v1')" 2>/dev/null || echo "http://localhost:8000/v1")

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
            echo "[INFO] Starting local vLLM server for '${LLM_MODEL}' on port 8000..."
            if command -v vllm >/dev/null 2>&1; then
                vllm serve "${LLM_MODEL}" --port 8000 --gpu-memory-utilization 0.90 --max-model-len 32768 &
            else
                python -m vllm.entrypoints.openai.api_server --model "${LLM_MODEL}" --port 8000 --gpu-memory-utilization 0.90 --max-model-len 32768 &
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

    # Execute Phase 2 Multi-Agent LLM Synthesis
    echo "[INFO] Executing Phase 2 Multi-Agent LLM Curriculum Synthesis..."
    python /app/run_pipeline.py "${CONFIG_FILE}" --phase 2
fi

echo "=================================================="
echo "All Pipeline Stages Completed Successfully!"
echo "=================================================="
