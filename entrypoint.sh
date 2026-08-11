#!/bin/bash

# Run the pipeline with whatever YAML is passed in, using exec to forward signals and quotes to protect paths
exec python /app/run_pipeline.py "$1"