FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

LABEL org.opencontainers.image.source="https://github.com/macronex/rfpeptides_mcp"
LABEL org.opencontainers.image.description="RFDiffusion All-Atom for cyclic peptide backbone generation"

ENV DEBIAN_FRONTEND=noninteractive
ENV DGLBACKEND=pytorch

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git wget build-essential && \
    rm -rf /var/lib/apt/lists/*

# Pin torch to the version shipped in the base image so pip doesn't
# upgrade it and pull in multi-GB nvidia-cu12 / triton packages.
RUN pip install --no-cache-dir \
    "torch==2.1.0" \
    fastmcp loguru click pandas numpy tqdm biopython \
    hydra-core omegaconf e3nn \
    icecream assertpy decorator pyrsistent

# DGL with CUDA 11.8
RUN pip install --no-cache-dir "torchdata==0.7.1" "dgl==2.1.0+cu118" -f https://data.dgl.ai/wheels/cu118/repo.html

# Clone RFDiffusion from public RosettaCommons repo
RUN git clone https://github.com/RosettaCommons/RFdiffusion.git /app/repo/RFdiffusion

# Install SE3-Transformer first (required dependency of rfdiffusion)
RUN cd /app/repo/RFdiffusion/env/SE3Transformer && \
    pip install --no-cache-dir -e .

# Install RFDiffusion (--no-deps since torch + se3-transformer already installed)
RUN cd /app/repo/RFdiffusion && \
    pip install --no-cache-dir --no-deps -e .

# Remove build tools no longer needed at runtime
RUN apt-get purge -y build-essential && apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Copy MCP server source
COPY --chmod=755 src/ src/

# Create mount point for model weights (mounted at runtime from cache)
RUN mkdir -p /app/repo/RFdiffusion/models

# Create writable directories for jobs/results
RUN mkdir -p /app/jobs /app/results && chmod 777 /app /app/jobs /app/results

ENV RFPEPTIDES_RFDIFF_DIR=/app/repo/RFdiffusion
ENV NVIDIA_CUDA_END_OF_LIFE=0
ENTRYPOINT []
CMD ["python", "src/server.py"]
