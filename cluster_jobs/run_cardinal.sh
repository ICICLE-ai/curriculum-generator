#!/bin/bash
# ==============================================================================
# SLURM Batch Job Script for DigitalAgEdu AI Pipeline on OSC Cardinal
# ==============================================================================
#SBATCH --job-name=cardinal_test
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cluster=cardinal
#SBATCH --account=PAS2699
#SBATCH --output=cardinal_test.out

# --- HARDWARE CONFIGURATION ---
# We are currently guessing these constraints. If "Requested node configuration is not available",
# try changing these based on Cardinal's rules:
#SBATCH --partition=gpu
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=26
#SBATCH --mem=64G

# (If the above fails, uncomment the lines below to request an ENTIRE Cardinal node instead)
# #SBATCH --partition=gpu
# #SBATCH --gpus-per-node=4
# #SBATCH --cpus-per-task=104
# #SBATCH --mem=512G
# ------------------------------

# Navigate to the directory where the job was submitted
cd $SLURM_SUBMIT_DIR

# ------------------------------------------------------------------------------
# OPTION A: Run using Apptainer (Highly Recommended!)
# This uses the exact same container Tapis uses, avoiding any Python/CUDA 
# module issues or AMD vs Intel CPU architecture crashes.
# ------------------------------------------------------------------------------
echo "Running via Apptainer..."
export APPTAINER_CACHEDIR="/fs/scratch/PAS2699/apptainer_cache"
export HF_HOME="/fs/ess/PAS2699/huggingface_cache"
export TORCH_HOME="/fs/ess/PAS2699/torch_cache"

apptainer run --nv docker://jassehxia/digital-age-edu:latest skin_cancer_config.yaml

# ------------------------------------------------------------------------------
# OPTION B: Run using Bare-Metal Virtual Environment
# (Comment out Option A and uncomment this if you prefer the local venv)
# ------------------------------------------------------------------------------
# module load python/3.10
# module load cuda/12.1.1
# if [ -d ".venv" ]; then
#     source .venv/bin/activate
# elif [ -d "venv_osc" ]; then
#     source venv_osc/bin/activate
# fi
# python run_pipeline.py skin_cancer_config.yaml
