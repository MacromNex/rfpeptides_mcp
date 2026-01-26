#!/bin/bash
# Quick Setup Script for RFpeptides MCP
# RFdiffusion-based cyclic peptide backbone generation
# Based on: https://github.com/RosettaCommons/RFdiffusion

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Setting up RFpeptides MCP ==="

# Check for mamba/conda
if command -v mamba >/dev/null 2>&1; then
    CONDA_CMD="mamba"
elif command -v conda >/dev/null 2>&1; then
    CONDA_CMD="conda"
else
    echo "Error: mamba or conda is required for RFpeptides setup"
    exit 1
fi

# Step 1: Create MCP environment (for fastmcp server)
echo "[1/5] Creating MCP Python 3.10 environment..."
$CONDA_CMD create -p ./env python=3.10 pip -y

# Step 2: Install fastmcp and dependencies
echo "[2/5] Installing fastmcp and dependencies..."
./env/bin/pip install fastmcp loguru

# Step 3: Create RFpeptides environment (for RFdiffusion)
echo "[3/5] Creating RFpeptides Python 3.9 environment..."
$CONDA_CMD create -p ./env_rfpeptides python=3.9 pip -y

# Step 4: Install PyTorch and RFdiffusion dependencies
echo "[4/5] Installing PyTorch and RFdiffusion dependencies..."
$CONDA_CMD install -p ./env_rfpeptides pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia -y
$CONDA_CMD install -p ./env_rfpeptides -c dglteam/label/cu118 dgl -y

# Install other dependencies
./env_rfpeptides/bin/pip install \
    hydra-core \
    pyrsistent \
    pandas \
    biopython \
    e3nn \
    opt_einsum_fx

# Step 5: Clone RFdiffusion if not present
echo "[5/5] Setting up RFdiffusion..."
if [ ! -d "repo/rfd_macro" ]; then
    mkdir -p repo
    echo "Please clone RFdiffusion with macrocycle support to repo/rfd_macro:"
    echo "  git clone https://github.com/RosettaCommons/RFdiffusion.git repo/rfd_macro"
    echo ""
    echo "Or create a symlink to an existing installation:"
    echo "  ln -s /path/to/rfd_macro repo/rfd_macro"
else
    echo "RFdiffusion already present at repo/rfd_macro"
fi

# Install SE(3)-Transformer
if [ -d "repo/rfd_macro" ]; then
    cd repo/rfd_macro
    ./env_rfpeptides/bin/pip install -e env/SE3Transformer 2>/dev/null || true
    cd "$SCRIPT_DIR"
fi

echo ""
echo "=== RFpeptides MCP Setup Complete ==="
echo ""
echo "Directory Structure:"
echo "  ./env              - MCP server environment (Python 3.10)"
echo "  ./env_rfpeptides   - RFdiffusion environment (Python 3.9)"
echo "  ./repo/rfd_macro   - RFdiffusion code"
echo ""
echo "To run the MCP server:"
echo "  ./env/bin/python -m src.server"
echo ""
echo "To test the installation:"
echo "  ./env/bin/python -c \"from src.server import mcp; print('OK')\""
echo ""
echo "To install as Claude Code MCP:"
echo "  fastmcp install claude-code src/server.py --name rfpeptides_mcp"
