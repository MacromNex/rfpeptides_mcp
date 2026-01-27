# RFpeptides MCP

> MCP tools for cyclic peptide design using RFpeptides

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Local Usage (Scripts)](#local-usage-scripts)
- [MCP Server Installation](#mcp-server-installation)
- [Using with Claude Code](#using-with-claude-code)
- [Available Tools](#available-tools)

## Overview

This MCP server provides computational tools for cyclic peptide backbone generation using RFdiffusion with cyclically symmetric position encodings. The server offers both fast synchronous operations and long-running asynchronous jobs for comprehensive cyclic peptide design workflows.

### Features

#### Backbone Generation Tools
| Tool | Description |
|------|-------------|
| `submit_cyclic_backbone` | Generate unconditional cyclic peptide backbones for structural space enumeration |
| `submit_cyclic_binder` | Design cyclic peptide binder backbones against a target protein |
| `submit_cyclic_binder_with_hotspots` | Design cyclic binder backbones with epitope-specific hotspot targeting |

#### Job Management Tools
| Tool | Description |
|------|-------------|
| `get_job_status` | Get status, timestamps, queue position, and errors for a submitted job |
| `get_job_result` | Retrieve output PDB file paths and results from a completed job |
| `get_job_log` | Get log output from a running or completed job |
| `list_jobs` | List all submitted jobs with optional status filtering |
| `get_queue_info` | Get current queue size, running job, and job counts by status |
| `cancel_job` | Cancel a pending or running job |
| `resubmit_job` | Resubmit a failed or cancelled job with the same parameters |

#### Utility Tools
| Tool | Description |
|------|-------------|
| `validate_pdb_file` | Validate PDB file structure and get chain/residue information |
| `get_server_info` | Get server information and list of available tools |


## Installation

### Quick Setup

Run the automated setup script:

```bash
./quick_setup.sh
```

This will create the environment and install all dependencies automatically.

Please view [`quick_setup.sh`](./quick_setup.sh) for manual installation steps.

## Local Usage (Scripts)

You can use the scripts directly without MCP for local processing. Below are demo cases for all 6 use cases from the RFpeptides paper.

### Use Case Overview

| # | Use Case | Description | Script |
|---|----------|-------------|--------|
| 1 | Diverse Binding Sites | Design for different pocket topologies | `run_binder_design.py` |
| 2 | AI-Predicted Structures | Design without experimental structure | `run_binder_design.py` |
| 3 | Epitope-Specific | Target specific residues with hotspots | `run_epitope_design.py` |
| 4 | Rapid Discovery | High-throughput with filtering | `run_binder_design.py` |
| 5 | Atomic Accuracy | Compare to X-ray structures | (validation step) |
| 6 | Structural Enumeration | Explore macrocyclic space | `run_backbone_enumeration.py` |

---

### Use Case 1: Diverse Binding Sites

Design cyclic peptide binders for different pocket topologies (concave helical, mixed alpha/beta, flat surface).

```bash
# MCL1 - Concave helical BH3-binding groove (12-16 residues)
python scripts/run_binder_design.py --target mcl1 --num-designs 50

# MDM2 - Concave helical p53-binding pocket (16-18 residues)
python scripts/run_binder_design.py --target mdm2 --num-designs 50

# GABARAP - Mixed alpha/beta LIR-docking site (13-18 residues)
python scripts/run_binder_design.py --target gabarap --num-designs 50

# Custom target with specific parameters
python scripts/run_binder_design.py \
    --pdb examples/structures/targets/2PQK.pdb \
    --chain A \
    --residue-range 203 321 \
    --binder-length 12 16 \
    --num-designs 100

# With --wait flag to wait for completion
python scripts/run_binder_design.py --target mcl1 --num-designs 2 --wait
```

**Parameters:**
- `--target`: Predefined target name (mcl1, mdm2, gabarap, rbta)
- `--pdb`: Path to custom target PDB file
- `--chain`: Target chain ID (Default: A)
- `--residue-range`: Target residue range START END (Default: auto-detect)
- `--binder-length`: Binder length range MIN MAX (Default: 12 16)
- `--num-designs`: Number of designs to generate (Default: 50)
- `--diffusion-steps`: Number of diffusion timesteps (Default: 50)
- `--wait`: Wait for job to complete before exiting (Default: False)

---

### Use Case 2: AI-Predicted Structures

Design binders for targets without experimental structures, using AlphaFold2 or RoseTTAFold predictions.

```bash
# RbtA - AI-predicted apo structure with flat binding surface
python scripts/run_binder_design.py --target rbta --num-designs 50

# Custom AlphaFold-predicted structure
python scripts/run_binder_design.py \
    --pdb /path/to/alphafold_prediction.pdb \
    --chain A \
    --binder-length 14 18 \
    --num-designs 100

# List all available predefined targets
python scripts/run_binder_design.py --list-targets
```

**Notes:**
- AI-predicted structures work well for binder design
- Consider using longer binders (14-18 residues) for flat surfaces
- May require more designs due to structural uncertainty

---

### Use Case 3: Epitope-Specific Targeting

Design binders that specifically interact with designated hotspot residues.

```bash
# GABARAP LIR-docking site hotspots (Lys46, Lys48, Tyr49, Leu50, Phe60, Leu63)
python scripts/run_epitope_design.py --target gabarap --num-designs 50

# MCL1 BH3-binding groove hotspots (Met231, Phe228, Leu267, Leu270, Gly271, Val274)
python scripts/run_epitope_design.py --target mcl1 --num-designs 50

# Custom hotspots on any target
python scripts/run_epitope_design.py \
    --pdb examples/structures/targets/3D32.pdb \
    --chain A \
    --hotspots 46 48 49 50 60 63 \
    --binder-length 13 18 \
    --num-designs 100

# RbtA surface epitope targeting
python scripts/run_epitope_design.py \
    --pdb examples/structures/targets/9CDV.pdb \
    --chain A \
    --hotspots 85 86 87 120 121 \
    --binder-length 14 18 \
    --num-designs 50

# List targets with predefined hotspots
python scripts/run_epitope_design.py --list-targets
```

**Parameters:**
- `--target`: Predefined target with hotspots (gabarap, mcl1, rbta)
- `--pdb`: Path to custom target PDB file
- `--hotspots`: Residue numbers to target (space-separated)
- `--binder-length`: Binder length range MIN MAX (Default: 13 18)
- `--num-designs`: Number of designs to generate (Default: 50)
- `--wait`: Wait for job to complete before exiting (Default: False)

**Hotspot Selection Tips:**
- Choose residues at protein-protein interfaces
- Target functionally important residues
- Include residues forming the binding pocket

---

### Use Case 4: Rapid Discovery (High-Throughput)

Generate large numbers of binder candidates for comprehensive screening.

```bash
# Large-scale MCL1 binder generation
python scripts/run_binder_design.py \
    --target mcl1 \
    --num-designs 1000 \
    --job-name "mcl1_large_scale"

# Multi-target screening (run sequentially or in parallel on multiple GPUs)
python scripts/run_binder_design.py --target mcl1 --num-designs 500
python scripts/run_binder_design.py --target mdm2 --num-designs 500
python scripts/run_binder_design.py --target gabarap --num-designs 500
python scripts/run_binder_design.py --target rbta --num-designs 500

# High-diversity generation with more diffusion steps
python scripts/run_binder_design.py \
    --target gabarap \
    --num-designs 500 \
    --diffusion-steps 100
```

**Recommended Filtering Pipeline (post-generation):**
1. Sequence design with LigandMPNN (8 sequences per backbone)
2. Structure validation with AfCycDesign (pLDDT > 0.8, RMSD < 2.0 Å)
3. Binding analysis (iPAE < 0.15)
4. Clustering by structural similarity

---

### Use Case 5: Atomic Accuracy Validation

Compare designed structures to experimentally validated X-ray complexes.

```bash
# The validation structures are in examples/structures/complexes/
# These are X-ray structures of designed cyclic peptides bound to targets:
#   9CDT - MCB_D2:MCL1 complex (2.1 Å)
#   9CDU - RBB_D10:RbtA complex (2.6 Å)
#   9HGC - GAB_D8:GABARAPL1 complex
#   9HGD - GAB_D23:GABARAP complex (1.5 Å)

# Generate new designs for comparison
python scripts/run_binder_design.py --target mcl1 --num-designs 100

# After getting results, compare backbone RMSD to validated complexes
# (Use PyMOL, TMalign, or other structure comparison tools)
```

**Validation Metrics:**
- Backbone RMSD < 1.5 Å to designed model
- pLDDT > 0.8 for high-confidence regions
- Interface contacts preserved

---

### Use Case 6: Structural Space Enumeration

Generate diverse cyclic peptide backbones without a target (unconditional generation).

```bash
# Generate 100 fixed-length 10-mer cyclic backbones
python scripts/run_backbone_enumeration.py --length 10 --num-designs 100

# Generate variable-length backbones (8-12 residues)
python scripts/run_backbone_enumeration.py --length 8 12 --num-designs 500

# Comprehensive enumeration for scaffold library
python scripts/run_backbone_enumeration.py --length 10 --num-designs 10000

# High-quality generation with more diffusion steps
python scripts/run_backbone_enumeration.py \
    --length 12 \
    --num-designs 100 \
    --diffusion-steps 100

# Multi-length scaffold library generation
for len in 8 10 12 14 16; do
    python scripts/run_backbone_enumeration.py \
        --length $len \
        --num-designs 1000 \
        --job-name "scaffold_${len}mer"
done
```

**Parameters:**
- `--length`: Peptide length (single value or range MIN MAX)
- `--num-designs`: Number of designs to generate (Default: 100)
- `--diffusion-steps`: Number of diffusion timesteps (Default: 50)
- `--wait`: Wait for job to complete before exiting (Default: False)

**Post-Generation Pipeline:**
1. Design sequences with LigandMPNN (8 sequences per backbone)
2. Refold with AfCycDesign
3. Filter by self-consistency (pLDDT > 0.8, RMSD < 2.0 Å)
4. Cluster by TMscore to identify unique structures
5. Visualize with tSNE embedding

---

### Job Management

Monitor and manage running jobs.

```bash
# List all jobs
python scripts/manage_jobs.py list

# Filter by status
python scripts/manage_jobs.py list --status completed
python scripts/manage_jobs.py list --status failed

# Check job status
python scripts/manage_jobs.py status <job_id>

# Get job results (output files)
python scripts/manage_jobs.py result <job_id>

# View job log (last 50 lines)
python scripts/manage_jobs.py log <job_id>

# View full job log
python scripts/manage_jobs.py log <job_id> --tail 0

# Get queue information
python scripts/manage_jobs.py queue

# Cancel a running job
python scripts/manage_jobs.py cancel <job_id>

# Resubmit a failed job
python scripts/manage_jobs.py resubmit <job_id>

# Recover interrupted jobs (after system restart)
python scripts/manage_jobs.py recover
```

---

## MCP Server Installation

```shell
mamba activate ./env
fastmcp install claude-code src/server.py --name rfpeptides_mcp
```

## Using with Claude Code

After installing the MCP server, you can use it directly in Claude Code.

### Quick Start

```bash
# Start Claude Code
claude
```

### Example Prompts

#### Tool Discovery
```
What tools are available from rfpeptides?
```

#### Use Case 1: Diverse Binding Sites
```
Design cyclic peptide binders for MCL1 using submit_cyclic_binder with 12-16 residue length and 50 designs
```

#### Use Case 2: AI-Predicted Structure
```
Design binders for the RbtA target at @examples/structures/targets/9CDV.pdb
```

#### Use Case 3: Epitope-Specific Design
```
Submit a binder design job for GABARAP targeting hotspot residues 46, 48, 49, 50, 60, 63 using submit_cyclic_binder_with_hotspots
```

#### Use Case 4: Rapid Discovery
```
Generate 500 binder candidates for MDM2 for high-throughput screening
```

#### Use Case 6: Structural Enumeration
```
Generate 100 unconditional 10-mer cyclic peptide backbones using submit_cyclic_backbone
```

#### Job Management
```
Check the status of all running jobs
Then show me the logs for the most recent job
```

#### PDB Validation
```
Validate the PDB file @examples/structures/targets/3D32.pdb and show me the chain information
```

#### Complete Workflow
```
1. First validate @examples/structures/targets/2PQK.pdb
2. Then submit a binder design job for MCL1 with 12-16 residue binders
3. Check the job status periodically until it completes
4. Show me the results when done
```

## Available Tools

### Predefined Targets

| Target | PDB | Pocket Type | Binder Length | Use Cases |
|--------|-----|-------------|---------------|-----------|
| `mcl1` | 2PQK | Concave helical | 12-16 residues | 1, 3, 4 |
| `mdm2` | 4HFZ | Concave helical | 16-18 residues | 1, 4 |
| `gabarap` | 3D32 | Mixed alpha/beta | 13-18 residues | 1, 3, 4 |
| `rbta` | 9CDV | Flat surface | 14-18 residues | 2, 3, 4 |

### Hotspot-Guided Design

| Target | Hotspots | Description |
|--------|----------|-------------|
| `gabarap` | K46, K48, Y49, L50, F60, L63 | LIR-docking site |
| `mcl1` | M231, F228, L267, L270, G271, V274 | BH3-binding groove |
| `rbta` | Customizable | Surface epitope |

### Validated Complex Structures

| PDB | Complex | Resolution | Notes |
|-----|---------|------------|-------|
| 9CDT | MCB_D2:MCL1 | 2.1 Å | Designed cyclic peptide |
| 9CDU | RBB_D10:RbtA | 2.6 Å | Designed cyclic peptide |
| 9HGC | GAB_D8:GABARAPL1 | - | Designed cyclic peptide |
| 9HGD | GAB_D23:GABARAP | 1.5 Å | High-resolution complex |

### Quality Guidelines

- **Binder Length**: 12-18 residues typical, adjust based on target
- **Num Designs**: 50-100 for standard, 500+ for thorough exploration
- **Diffusion Steps**: 50 (default), 100 for higher diversity
- **Typical Runtime**: 5-30 min depending on num_designs

### Recommended Starting Points

| Purpose | Designs | Diffusion Steps | Runtime |
|---------|---------|-----------------|---------|
| Testing | 5 | 50 | ~2-5 min |
| Standard | 50 | 50 | ~10-20 min |
| Thorough | 500 | 50 | ~1-2 hours |
| Production | 5000+ | 50-100 | ~10+ hours |

## References

- RFpeptides paper: De novo macrocyclic peptide design using RFdiffusion
- RFdiffusion: https://github.com/RosettaCommons/RFdiffusion
