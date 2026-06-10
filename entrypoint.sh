#!/bin/bash

# Point to the HuggingFace cache so Phi-3 is permenently cached
export HF_HOME=/fs/ess/PAS2699/huggingface_cache

# Run the pipeline with whatever YAML is passed in
python run_pipeline.py $1