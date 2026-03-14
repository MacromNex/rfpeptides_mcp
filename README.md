# RFpeptides MCP Server

**Cyclic peptide backbone generation using RFdiffusion via Docker**

An MCP (Model Context Protocol) server for cyclic peptide design with 3 core backbone generation tools:
- Generate unconditional cyclic peptide backbones for structural space enumeration
- Design cyclic peptide binder backbones against a target protein
- Design cyclic binder backbones with epitope-specific hotspot targeting

Plus job management (status, results, logs, cancel, resubmit) and PDB validation utilities.

## Quick Start with Docker

### Approach 1: Pull Pre-built Image from GitHub

The fastest way to get started. A pre-built Docker image is automatically published to GitHub Container Registry on every release.

```bash
# Pull the latest image
docker pull ghcr.io/macromnex/rfpeptides_mcp:latest

# Register with Claude Code (runs as current user to avoid permission issues)
claude mcp add rfpeptides -- docker run -i --rm --user `id -u`:`id -g` --gpus all --ipc=host -v `pwd`:`pwd` ghcr.io/macromnex/rfpeptides_mcp:latest
```

**Note:** Run from your project directory. `` `pwd` `` expands to the current working directory.

**Note:** Model weights are **not** included in the Docker image. They must be mounted at runtime:

```bash
# With model weights mounted from local cache
claude mcp add rfpeptides -- docker run -i --rm --user `id -u`:`id -g` --gpus all --ipc=host \
  -v `pwd`:`pwd` \
  -v /path/to/macromnex_cache/model/rfpeptides/models:/app/repo/RFdiffusion/models:ro \
  ghcr.io/macromnex/rfpeptides_mcp:latest
```

**Requirements:**
- Docker with GPU support (`nvidia-docker` or Docker with NVIDIA runtime)
- Claude Code installed
- RFdiffusion model weights in your local cache

That's it! The RFpeptides MCP server is now available in Claude Code.

---

### Approach 2: Build Docker Image Locally

Build the image yourself and install it into Claude Code. Useful for customization or offline environments.

```bash
# Clone the repository
git clone https://github.com/MacromNex/rfpeptides_mcp.git
cd rfpeptides_mcp

# Build the Docker image
docker build -t rfpeptides_mcp:latest .

# Register with Claude Code (runs as current user to avoid permission issues)
claude mcp add rfpeptides -- docker run -i --rm --user `id -u`:`id -g` --gpus all --ipc=host \
  -v `pwd`:`pwd` \
  -v /path/to/macromnex_cache/model/rfpeptides/models:/app/repo/RFdiffusion/models:ro \
  rfpeptides_mcp:latest
```

**Note:** Run from your project directory. `` `pwd` `` expands to the current working directory.

**Requirements:**
- Docker with GPU support
- Claude Code installed
- Git (to clone the repository)

**About the Docker Flags:**
- `-i` — Interactive mode for Claude Code
- `--rm` — Automatically remove container after exit
- `` --user `id -u`:`id -g` `` — Runs the container as your current user, so output files are owned by you (not root)
- `--gpus all` — Grants access to all available GPUs
- `--ipc=host` — Uses host IPC namespace for better performance
- `-v` — Mounts your project directory and model weights

---

## Verify Installation

After adding the MCP server, you can verify it's working:

```bash
# List registered MCP servers
claude mcp list

# You should see 'rfpeptides' in the output
```

In Claude Code, you can now use all RFpeptides tools:
- `submit_cyclic_backbone` — Unconditional cyclic peptide generation
- `submit_cyclic_binder` — Cyclic binder design against a target
- `submit_cyclic_binder_with_hotspots` — Epitope-specific binder design
- `get_job_status` / `get_job_result` / `get_job_log` — Job monitoring
- `list_jobs` / `get_queue_info` / `cancel_job` / `resubmit_job` — Queue management
- `validate_pdb_file` / `get_server_info` — Utilities

---

## Next Steps

- **Detailed documentation**: See [detail.md](detail.md) for comprehensive guides on:
  - Available MCP tools and parameters
  - Local Python environment setup (alternative to Docker)
  - Example workflows and use cases for all 6 RFpeptides use cases
  - Predefined targets and hotspot configurations
  - Script-based usage without MCP

---

## Usage Examples

Once registered, you can use the RFpeptides tools directly in Claude Code:

### Example 1: Unconditional Backbone Generation

```
Generate 100 unconditional 10-mer cyclic peptide backbones using submit_cyclic_backbone
```

### Example 2: Binder Design Against a Target

```
Design cyclic peptide binders for the protein at /path/to/target.pdb with 12-16 residue length and 50 designs using submit_cyclic_binder
```

### Example 3: Epitope-Specific Binder Design

```
Submit a binder design job for GABARAP (examples/structures/targets/7ZKR.pdb) targeting hotspot residues 48, 50, 51, 52, 62, 65 using submit_cyclic_binder_with_hotspots
```

### Example 4: Job Monitoring

```
Check the status of all running jobs, then show me the logs for the most recent job
```

---

## Troubleshooting

**Docker not found?**
```bash
docker --version  # Install Docker if missing
```

**GPU not accessible?**
- Ensure NVIDIA Docker runtime is installed
- Check with `docker run --gpus all ubuntu nvidia-smi`

**Claude Code not found?**
```bash
# Install Claude Code
npm install -g @anthropic-ai/claude-code
```

**Model weights missing?**
- RFdiffusion model weights must be downloaded separately
- Place them in your `macromnex_cache/model/rfpeptides/models/` directory
- See [detail.md](detail.md) for model setup instructions

---

## References

- RFpeptides paper: De novo macrocyclic peptide design using RFdiffusion
- RFdiffusion: https://github.com/RosettaCommons/RFdiffusion

## License

MIT
