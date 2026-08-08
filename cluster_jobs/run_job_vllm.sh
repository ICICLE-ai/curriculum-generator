#!/bin/bash
#SBATCH --job-name=digitalagedu_full
#SBATCH --account=PAS2699
#SBATCH --gpus=1
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/fs/ess/PAS2699/jseh_workspace/curriculum_generator/slurm_%j.log
#SBATCH --error=/fs/ess/PAS2699/jseh_workspace/curriculum_generator/slurm_%j.err

# Change directory to the job submission folder
cd "${SLURM_SUBMIT_DIR:-/fs/ess/PAS2699/jseh_workspace/curriculum_generator}"

# Shared HuggingFace cache in workspace
export HF_HOME=/fs/ess/PAS2699/jseh_workspace/.cache/huggingface
export HUGGINGFACE_HUB_CACHE=/fs/ess/PAS2699/jseh_workspace/.cache/huggingface
export TRANSFORMERS_CACHE=/fs/ess/PAS2699/jseh_workspace/.cache/huggingface

# Compiler flags for native compilation
export CC=gcc
export CXX=g++
export NVCC_CCBIN=gcc

CONFIG_FILE="${1:-configs/skin_cancer_config.yaml}"
echo "=================================================="
echo "DigitalAgEdu Full Pipeline Job: ${CONFIG_FILE}"
echo "=================================================="

# Activate Python Virtual Environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

echo "Active Python Environment: $(which python)"

# Extract configured model name from YAML config (curriculum.model -> execution.llm_model -> root model)
MODEL_NAME=$(python -c "import yaml; cfg=yaml.safe_load(open('${CONFIG_FILE}')); curr=cfg.get('curriculum', {}); exec_c=cfg.get('execution', {}); print(curr.get('model') or exec_c.get('llm_model') or cfg.get('model') or 'Qwen/Qwen2.5-Coder-32B-Instruct-AWQ')")

# ==============================================================================
# STAGE 1: Start vLLM Endpoint Server (Background)
# ==============================================================================
echo "=================================================="
echo "STAGE 1: Starting local vLLM server for '${MODEL_NAME}'..."
echo "=================================================="
vllm serve "${MODEL_NAME}" --port 8000 --max-model-len 32768 &
VLLM_PID=$!

# Ensure vLLM process is killed when script exits or fails
trap 'echo "Terminating vLLM server PID $VLLM_PID..."; kill $VLLM_PID 2>/dev/null || true' EXIT

echo "Waiting for vLLM server HTTP endpoint on port 8000..."
until curl -s http://localhost:8000/v1/models > /dev/null; do
    sleep 5
done
echo "[SUCCESS] vLLM server is ready to process requests!"

# ==============================================================================
# STAGE 2: Execute Unified Pipeline (Phase 1 Vision DL + Phase 2 Autonomous LLM)
# ==============================================================================
echo "=================================================="
echo "STAGE 2: Executing Unified Pipeline (Phase 1 + Phase 2 LLM)..."
echo "=================================================="
python run_pipeline.py "${CONFIG_FILE}"

echo "=================================================="
echo "[SUCCESS] DigitalAgEdu Pipeline Job Completed Successfully!"
echo "=================================================="
