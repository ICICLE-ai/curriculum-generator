#!/bin/bash
# ==============================================================================
# SLURM Batch Job Script for DigitalAgEdu AI Pipeline on OSC Ascend
# ==============================================================================
#SBATCH --job-name=osc_pipeline_test
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=8
#SBATCH --cluster=ascend
#SBATCH --output=slurm-%j.out
#SBATCH --account=PAS2699

# Load necessary modules
module load python/3.10
module load cuda/12.1.1

# Navigate to the directory where the job was submitted
cd $SLURM_SUBMIT_DIR

# Activate the virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv_osc" ]; then
    source venv_osc/bin/activate
else
    echo "Warning: No virtual environment (.venv or venv_osc) found in current directory."
fi

# Run the AI pipeline
python run_pipeline.py skin_cancer_config.yaml
