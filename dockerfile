# Use a slim Python base image to keep the container lightweight
FROM python:3.9-slim

# 1. Install system dependencies and MinIO Client (mc)
# We update the package manager, install wget, download the mc binary,
# make it executable, and move it to a global path.
RUN apt-get update && apt-get install -y wget && \
    wget https://dl.min.io/client/mc/release/linux-amd64/mc && \
    chmod +x mc && \
    mv mc /usr/local/bin/ && \
    # Clean up apt cache to reduce image size
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 2. Install Python dependencies
# Ensure requirements.txt exists in the root directory before building
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Set the primary working directory inside the container
WORKDIR /workspace

# Set environment variable to allow Python to find config.py at the root level
ENV PYTHONPATH=/workspace