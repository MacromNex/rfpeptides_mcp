# RFpeptides Scripts

Command-line scripts for cyclic peptide backbone generation using RFdiffusion.

## Available Scripts

| Script | Purpose | Use Cases |
|--------|---------|-----------|
| `run_binder_design.py` | Design binders against a target | Cases 1, 2, 4 |
| `run_epitope_design.py` | Design binders with hotspot targeting | Case 3 |
| `run_backbone_enumeration.py` | Generate unconditional backbones | Case 6 |
| `manage_jobs.py` | Job monitoring and management | All |

## Quick Start

### 1. Design Binders for a Target Protein

```bash
# Use predefined target (MCL1, MDM2, GABARAP, RbtA)
python scripts/run_binder_design.py --target mcl1 --num-designs 50

# Use custom PDB
python scripts/run_binder_design.py --pdb /path/to/target.pdb --chain A --num-designs 100

# List available predefined targets
python scripts/run_binder_design.py --list-targets
```

### 2. Design Binders with Hotspot Targeting

```bash
# Use predefined target with known hotspots
python scripts/run_epitope_design.py --target gabarap --num-designs 50

# Use custom hotspots
python scripts/run_epitope_design.py --pdb target.pdb --hotspots 46 48 49 50 60 63 --num-designs 100

# List available targets with hotspots
python scripts/run_epitope_design.py --list-targets
```

### 3. Generate Unconditional Backbones

```bash
# Generate 100 10-mer cyclic backbones
python scripts/run_backbone_enumeration.py --length 10 --num-designs 100

# Generate variable-length backbones (8-12 residues)
python scripts/run_backbone_enumeration.py --length 8 12 --num-designs 500
```

### 4. Manage Jobs

```bash
# List all jobs
python scripts/manage_jobs.py list

# Check job status
python scripts/manage_jobs.py status <job_id>

# Get job results
python scripts/manage_jobs.py result <job_id>

# View job log
python scripts/manage_jobs.py log <job_id>

# Cancel a job
python scripts/manage_jobs.py cancel <job_id>

# Resubmit a failed job
python scripts/manage_jobs.py resubmit <job_id>
```

## Parameters Guide

### Binder Length Recommendations

| Target Type | Recommended Length | Notes |
|-------------|-------------------|-------|
| Concave helical | 12-18 residues | MCL1, MDM2 |
| Mixed alpha/beta | 13-18 residues | GABARAP |
| Flat surface | 14-20 residues | RbtA |
| Small pocket | 8-12 residues | |

### Number of Designs

| Purpose | Designs | Notes |
|---------|---------|-------|
| Quick test | 5-10 | Fast iteration |
| Standard | 50-100 | Good coverage |
| Thorough | 500-1000 | Better diversity |
| Production | 5000+ | Comprehensive |

### Diffusion Steps

| Quality | Steps | Notes |
|---------|-------|-------|
| Fast | 25 | Lower diversity |
| Standard | 50 | Good balance (default) |
| High | 100 | More diversity |

## Output

All job outputs are stored in the `jobs/` directory:

```
jobs/
└── <job_id>/
    ├── metadata.json     # Job configuration
    ├── job.log          # Execution log
    ├── result.json      # Output summary
    ├── *.pdb            # Generated structures
    └── *.trb            # Trajectory metadata
```

## Environment

Scripts use the RFpeptides environment at `../env_rfpeptides`. Ensure it's properly set up:

```bash
mamba run -p ./env_rfpeptides python -c "from rfdiffusion.inference import utils; print('OK')"
```
