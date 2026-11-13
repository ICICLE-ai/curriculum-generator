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

echo "Phase 1 completed successfully."

# ==============================================================================
# STAGE 2: Phase 2 LLM Curriculum Generator (NRP managed LLM API;
# key from the NRP_LLM_API env var, sent per job by the web app)
# ==============================================================================
echo "=================================================="
echo "STAGE 2: Executing Phase 2 LLM Curriculum Generator..."
echo "=================================================="
python -c "from digitalagedu.core.llm import generate_llm_curriculum; generate_llm_curriculum('${CONFIG_FILE}')"
echo "=================================================="
echo "[SUCCESS] DigitalAgEdu Full Pipeline Job Completed Successfully!"
echo "=================================================="
