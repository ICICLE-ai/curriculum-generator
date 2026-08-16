# 1. BUMP BASE IMAGE: Use a modern PyTorch image that matches modern vLLM/CUDA requirements
FROM pytorch/pytorch:2.5.1-cuda12.1-cudnn9-devel

# Set the working directory
WORKDIR /app

# Install system level dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements and install Python packages
COPY requirements.txt .

# 2. OPTIMIZE INSTALLATION: Leverage uv for everything to speed up building
RUN pip install uv
RUN uv pip install --system ninja

# 3. USE UV FOR REQUIREMENTS: It resolves complex ML dependencies significantly better than pip
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy the codebase into the container
# ML Pipeline
COPY digitalagedu/ /app/digitalagedu/
COPY curriculum_resources/ /app/curriculum_resources/
COPY run_pipeline.py /app/

# Set the entrypoint to the wrapper script
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
