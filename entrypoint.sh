#!/bin/bash

# Point to the HuggingFace cache so Phi-3 is permenently cached
export HF_HOME=/fs/ess/PAS2699/huggingface_cache

# Run the pipeline with whatever YAML is passed in, using exec to forward signals and quotes to protect paths
exec python /app/run_pipeline.py "$1"