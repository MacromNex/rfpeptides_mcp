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

# MCP server dependencies (Python 3.10 env)
RUN pip install --no-cache-dir \
    fastmcp loguru click pandas numpy tqdm biopython

# RFDiffusion dependencies
RUN pip install --no-cache-dir \
    hydra-core omegaconf e3nn wandb \
    icecream assertpy decorator \
    pyrsistent opt_einsum jax

# DGL with CUDA 11.8
RUN pip install --no-cache-dir dgl -f https://data.dgl.ai/wheels/cu118/repo.html

# Clone RFDiffusion from public RosettaCommons repo
RUN git clone https://github.com/RosettaCommons/RFdiffusion.git /app/repo/RFdiffusion && \
    cd /app/repo/RFdiffusion && \
    pip install --no-cache-dir -e .

# Install SE3-Transformer
RUN cd /app/repo/RFdiffusion/env/SE3Transformer && \
    pip install --no-cache-dir -e .

# Copy MCP server source
COPY --chmod=755 src/ src/

# Download RFdiffusion model weights (done at build time for reproducibility)
RUN mkdir -p /app/repo/RFdiffusion/models && \
    wget -q -O /app/repo/RFdiffusion/models/RFdiffusion_aa.pt \
    https://files.ipd.uw.edu/dimaio/RFdiffusion_aa.pt || true

# Create writable directories for jobs/results
RUN mkdir -p /app/jobs /app/results && chmod 777 /app /app/jobs /app/results

ENV NVIDIA_CUDA_END_OF_LIFE=0
ENTRYPOINT []
CMD ["python", "src/server.py"]
