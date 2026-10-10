#!/bin/bash
#SBATCH --job-name=digitalagedu_full
#SBATCH --account=PAS2699
#SBATCH --gpus=1
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=64G
#SBATCH --time=05:00:00
#SBATCH --output=/fs/ess/PAS2699/jseh_workspace/curriculum_generator/slurm_%j.log
#SBATCH --error=/fs/ess/PAS2699/jseh_workspace/curriculum_generator/slurm_%j.err

# Change directory to the job submission folder
cd "${SLURM_SUBMIT_DIR:-/fs/ess/PAS2699/jseh_workspace/curriculum_generator}"

# Shared HuggingFace cache & W&B offline mode in workspace

# Compiler flags for native compilation
export CC=gcc
export CXX=g++
export NVCC_CCBIN=gcc

CONFIG_FILE="${1:-configs/skin_cancer_config.yaml}"
echo "=================================================="
echo "DigitalAgEdu Full Pipeline Job: ${CONFIG_FILE}"
echo "=================================================="

# ==============================================================================
# STAGE 1: Computer Vision & Telemetry Pipeline (Phase 1)
# ==============================================================================
echo "=================================================="
echo "STAGE 1: Loading Phase 1 CUDA & PyTorch Modules..."
echo "=================================================="
module load python/3.10 cuda/12.1.1 2>/dev/null || module load python cuda 2>/dev/null || true

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

echo "Phase 1 Active Python: $(which python)"
echo "Executing Phase 1 Vision DL Pipeline..."
python run_pipeline.py "${CONFIG_FILE}"

echo "Phase 1 completed successfully. Deactivating Phase 1 environment..."
deactivate 2>/dev/null || true

# ==============================================================================
# STAGE 2: Mid-Job Switch to vLLM & Launch Server (Phase 2)
# ==============================================================================
echo "=================================================="
echo "STAGE 2: Loading vLLM Module & Starting Server..."
echo "=================================================="
module unload python cuda 2>/dev/null || true
module load vllm/0.23.0 2>/dev/null || module load vllm 2>/dev/null || true

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

echo "Phase 2 Active Python: $(which python)"

# Extract configured model name from YAML config (curriculum.model -> execution.llm_model -> root model)
MODEL_NAME=$(python -c "import yaml; cfg=yaml.safe_load(open('${CONFIG_FILE}')); curr=cfg.get('curriculum', {}); exec_c=cfg.get('execution', {}); print(curr.get('model') or exec_c.get('llm_model') or cfg.get('model') or 'Qwen/Qwen2.5-Coder-32B-Instruct-AWQ')")

echo "Starting local vLLM server for model '${MODEL_NAME}' on port 8000..."
if command -v vllm >/dev/null 2>&1; then
    vllm serve "${MODEL_NAME}" --port 8000 --max-model-len 32768 &
else
    python -m vllm.entrypoints.openai.api_server --model "${MODEL_NAME}" --port 8000 --max-model-len 32768 &
fi
VLLM_PID=$!

# Ensure vLLM process is killed when script exits or fails
trap 'echo "Terminating vLLM server PID $VLLM_PID..."; kill $VLLM_PID 2>/dev/null || true' EXIT

echo "Waiting for vLLM server HTTP endpoint on port 8000 (PID: $VLLM_PID)..."
MAX_WAIT_SECONDS=300
ELAPSED=0
until curl -s http://localhost:8000/v1/models > /dev/null 2>&1; do
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
echo "[SUCCESS] vLLM server is ready to process requests!"

# ==============================================================================
# STAGE 3: Autonomous LLM Curriculum Generator
# ==============================================================================
echo "=================================================="
echo "STAGE 3: Executing Phase 2 LLM Curriculum Generator..."
echo "=================================================="
python -c "from digitalagedu.core.llm import generate_llm_curriculum; generate_llm_curriculum('${CONFIG_FILE}')"

# ==============================================================================
# STAGE 4: Job Cleanup
# ==============================================================================
echo "=================================================="
echo "STAGE 4: Cleaning Up Background Processes..."
echo "=================================================="
kill $VLLM_PID 2>/dev/null || true
echo "=================================================="
echo "[SUCCESS] DigitalAgEdu Full Pipeline Job Completed Successfully!"
echo "=================================================="
