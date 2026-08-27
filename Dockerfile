#Pinned Presenton AI presentation engine (pinned to v0.9.7-beta on linux/amd64)
FROM --platform=linux/amd64 ghcr.io/presenton/presenton:v0.9.7-beta AS presenton_stage

# Main DigitalAgEdu CUDA / PyTorch image (enforcing linux/amd64 for HPC clusters)
FROM --platform=linux/amd64 pytorch/pytorch:2.5.1-cuda12.1-cudnn9-devel

# Set the working directory
WORKDIR /app

# Install system level dependencies, Node.js 20, and Google Chrome for Presenton headless export
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    git \
    wget \
    curl \
    gnupg \
    ca-certificates \
    fonts-liberation \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm -f google-chrome-stable_current_amd64.deb \
    && ln -sf /usr/bin/google-chrome-stable /usr/bin/chromium \
    && rm -rf /var/lib/apt/lists/*

# Configure headless Puppeteer / Chromium paths for Presenton presentation export
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/google-chrome-stable
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV CHROMIUM_PATH=/usr/bin/google-chrome-stable

# Copy the requirements and install Python packages
COPY requirements.txt .

RUN pip install uv
RUN uv pip install --system ninja
RUN uv pip install --system --no-cache -r requirements.txt

# Copy Presenton runtime assets from pinned stage
COPY --from=presenton_stage /app /app/presenton

# Ensure all Presenton template assets, fonts, and scripts are universally readable
RUN chmod -R a+rX /app/presenton

# Install Presenton backend package & all declared dependencies into Python environment
RUN uv pip install --system /app/presenton/servers/fastapi


# Copy the codebase into the container
# ML Pipeline
COPY digitalagedu/ /app/digitalagedu/
COPY curriculum_resources/ /app/curriculum_resources/
COPY run_pipeline.py /app/

# Set the entrypoint to the wrapper script
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
