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

CONFIG_FILE="${1:-skin_cancer_config.yaml}"
echo "Running full pipeline with config: ${CONFIG_FILE}"

# ==============================================================================
# STAGE 1: Computer Vision & Telemetry Pipeline (DINOv2, SAM, Visual XAI)
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
echo "Executing Phase 1 Vision Pipeline..."
python run_pipeline.py "${CONFIG_FILE}"

# Process termination automatically clears GPU VRAM
echo "Phase 1 completed successfully. Deactivating Phase 1 environment..."
deactivate 2>/dev/null || true

# ==============================================================================
# STAGE 2: Mid-Job Module Switch to vLLM & Server Launch
# ==============================================================================
echo "=================================================="
echo "STAGE 2: Switching Modules to vLLM Server..."
echo "=================================================="
module unload python cuda 2>/dev/null || true
module load vllm/0.23.0 2>/dev/null || module load vllm 2>/dev/null || module load python/3.12 2>/dev/null || true

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

echo "Phase 2 Active Python: $(which python)"

# Extract configured model name from YAML config
MODEL_NAME=$(python -c "import yaml; cfg=yaml.safe_load(open('${CONFIG_FILE}')); print(cfg.get('curriculum', {}).get('model') or cfg.get('model') or 'Qwen/Qwen2.5-Coder-32B-Instruct-AWQ')")

echo "Starting local vLLM server for model '${MODEL_NAME}' on port 8000..."
vllm serve "${MODEL_NAME}" --port 8000 --max-model-len 32768 &
VLLM_PID=$!

# Wait until vLLM is ready to accept HTTP requests
echo "Waiting for vLLM server endpoint..."
until curl -s http://localhost:8000/v1/models > /dev/null; do
    sleep 5
done
echo "vLLM server ready!"

# ==============================================================================
# STAGE 3: Autonomous LLM Curriculum Generator
# ==============================================================================
echo "=================================================="
echo "STAGE 3: Executing Phase 2 LLM Curriculum Generator..."
echo "=================================================="
if [ -f "main.py" ]; then
    python main.py
else
    python test_generator.py
fi

# ==============================================================================
# STAGE 4: Job Cleanup
# ==============================================================================
echo "=================================================="
echo "STAGE 4: Cleaning Up Background Processes..."
echo "=================================================="
kill $VLLM_PID
echo "[SUCCESS] Full Pipeline Execution Completed!"
