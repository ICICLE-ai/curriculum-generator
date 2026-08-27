#!/bin/bash
set -e

CONFIG_FILE="${1:-sample_config.yaml}"

# 0. Enforce container-internal standard GCC compilers (prevents host HPC Spack leakage)
export CC=gcc
export CXX=g++
export NVCC_CCBIN=gcc

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

    # 2.2 Start local Presenton slide generator daemon on port 5001
    if [ -d "/app/presenton/servers/fastapi" ] || [ -d "/app/presenton" ] || command -v presenton >/dev/null 2>&1; then
        echo "[INFO] Starting local Presenton slide generator daemon on port 5001..."
        export APP_DATA_DIRECTORY="/tmp/presenton_data"
        export DATA_DIR="/tmp/presenton_data"
        export USER_CONFIG_PATH="/tmp/presenton_data/userConfig.json"
        export MIGRATE_DATABASE_ON_STARTUP=true
        export DISABLE_AUTH=true
        export AUTH_REQUIRED=false
        export AUTH_USERNAME=admin
        export AUTH_PASSWORD=AdminPassword123!
        export LLM=custom
        export CUSTOM_LLM_URL="${LLM_BASE_URL}"
        export CUSTOM_LLM_API_KEY="none"
        export CUSTOM_MODEL="${LLM_MODEL}"
        export OPENAI_BASE_URL="${LLM_BASE_URL}"
        export OPENAI_API_BASE="${LLM_BASE_URL}"
        export OPENAI_MODEL="${LLM_MODEL}"
        export OPENAI_API_KEY="none"
        export DISABLE_IMAGE_GENERATION=true
        export IMAGE_PROVIDER=none
        export PUPPETEER_EXECUTABLE_PATH="${PUPPETEER_EXECUTABLE_PATH:-/usr/bin/google-chrome-stable}"
        export PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
        export CHROMIUM_PATH="${CHROMIUM_PATH:-/usr/bin/google-chrome-stable}"
        mkdir -p /tmp/presenton_data
        if [ -f "/app/scripts/patch_presenton_schemas.py" ]; then
            python /app/scripts/patch_presenton_schemas.py || true
        fi
        if [ -d "/app/presenton/servers/fastapi" ]; then
            python -m uvicorn api.main:app --app-dir /app/presenton/servers/fastapi --port 5001 --host 127.0.0.1 &
        elif [ -d "/app/presenton" ]; then
            python -m uvicorn api.main:app --app-dir /app/presenton --port 5001 --host 127.0.0.1 &
        else
            python -m uvicorn presenton.main:app --port 5001 --host 127.0.0.1 &
        fi
        PRESENTON_PID=$!
        trap 'echo "[INFO] Cleaning up background processes..."; kill $VLLM_PID $PRESENTON_PID 2>/dev/null || true' EXIT

        echo "[INFO] Waiting for Presenton slide generator on port 5001 (PID: $PRESENTON_PID)..."
        MAX_WAIT_PRESENTON=60
        ELAPSED_PRESENTON=0
        until python -c "import urllib.request; urllib.request.urlopen('http://localhost:5001/docs', timeout=2)" > /dev/null 2>&1; do
            if ! kill -0 $PRESENTON_PID 2>/dev/null; then
                echo "[ERROR] Presenton daemon process ($PRESENTON_PID) exited or failed to start."
                exit 1
            fi
            if [ $ELAPSED_PRESENTON -ge $MAX_WAIT_PRESENTON ]; then
                echo "[ERROR] Timed out after ${MAX_WAIT_PRESENTON}s waiting for Presenton slide daemon to start."
                exit 1
            fi
            sleep 2
            ELAPSED_PRESENTON=$((ELAPSED_PRESENTON + 2))
        done
        echo "[SUCCESS] Presenton slide generator daemon is ready on port 5001!"
    fi

    # Execute Phase 2 Multi-Agent LLM Synthesis
    echo "[INFO] Executing Phase 2 Multi-Agent LLM Curriculum Synthesis..."
    python /app/run_pipeline.py "${CONFIG_FILE}" --phase 2
fi

echo "=================================================="
echo "All Pipeline Stages Completed Successfully!"
echo "=================================================="
