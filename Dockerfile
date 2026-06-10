# Using the official PyTorch image with CUDA 12.1 preinstalled
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-devel

# Set the working directory
WORKDIR /app

# Install system Level dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements and install Python packages
COPY requirements.txt .
RUN pip install uv
RUN uv pip install --system ninja
RUN uv pip install --system --no-cache --no-build-isolation -r requirements.txt

# Copy the codebase into the container

# ML Pipeline
COPY digitalagedu/ /app/digitalagedu/
COPY curriculum_resources/ /app/curriculum_resources/
COPY run_pipeline.py /app/

# Set the entrypoint to the wrapper script
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
