# RFpeptides Scripts

Command-line scripts for cyclic peptide backbone generation using RFdiffusion.
These scripts run directly as local jobs (no job queue) and output to the `results/` directory by default.

## Available Scripts

| Script | Purpose | Use Cases | Default Output |
|--------|---------|-----------|----------------|
| `run_binder_design.py` | Design binders against a target (linear or cyclic) | Cases 1, 2, 4 | `results/binder_outputs/` |
| `run_epitope_design.py` | Design binders with hotspot targeting (linear or cyclic) | Case 3 | `results/epitope_outputs/` |
| `run_backbone_enumeration.py` | Generate unconditional cyclic backbones | Case 6 | `results/backbone_outputs/` |

## Quick Start

### 1. Design Binders for a Target Protein

```bash
# Design linear binders for MCL1 (predefined target)
python scripts/run_binder_design.py --target mcl1 --num-designs 50

# Design cyclic binders for MCL1
python scripts/run_binder_design.py --target mcl1 --num-designs 50 --cyclic

# Use custom PDB
python scripts/run_binder_design.py --pdb /path/to/target.pdb --chain A --num-designs 100

# Custom output directory with cyclic binders
python scripts/run_binder_design.py --target gabarap --num-designs 20 --cyclic --output-dir ./my_outputs

# List available predefined targets
python scripts/run_binder_design.py --list-targets
```

### 2. Design Binders with Hotspot Targeting

```bash
# Design linear binders targeting GABARAP LIR-docking site
python scripts/run_epitope_design.py --target gabarap --num-designs 50

# Design cyclic binders targeting GABARAP
python scripts/run_epitope_design.py --target gabarap --num-designs 50 --cyclic

# Use custom hotspots
python scripts/run_epitope_design.py --pdb target.pdb --hotspots 46 48 49 50 60 63 --num-designs 100

# Custom output directory with cyclic binders
python scripts/run_epitope_design.py --target mcl1 --num-designs 20 --cyclic --output-dir ./my_outputs

# List available targets with hotspots
python scripts/run_epitope_design.py --list-targets
```

### 3. Generate Unconditional Backbones

```bash
# Generate 100 10-mer cyclic backbones
python scripts/run_backbone_enumeration.py --length 10 --num-designs 100

# Generate variable-length backbones (8-12 residues)
python scripts/run_backbone_enumeration.py --length 8 12 --num-designs 500

# Custom output directory
python scripts/run_backbone_enumeration.py --length 10 --num-designs 50 --output-dir ./my_outputs
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

### GPU Device Selection

All scripts support the `--device` parameter to select which CUDA GPU to use:

```bash
# Use GPU 0
python scripts/run_binder_design.py --target mcl1 --num-designs 50 --device 0

# Use GPU 1
python scripts/run_backbone_enumeration.py --length 10 --num-designs 100 --device 1

# Use default GPU (no --device flag)
python scripts/run_epitope_design.py --target gabarap --num-designs 50
```

This sets `CUDA_VISIBLE_DEVICES` internally. If `--device` is not specified, the default GPU is used.

## Output

All outputs are stored in the `results/` directory by default:

```
results/
├── backbone_outputs/    # Unconditional backbone generation
│   ├── cyclic_10mer_0.pdb
│   ├── cyclic_10mer_0.trb
│   └── ...
├── binder_outputs/      # Target binder design
│   ├── 2PQK_binder_0.pdb
│   ├── 2PQK_binder_0.trb
│   └── ...
└── epitope_outputs/     # Hotspot-guided design
    ├── 3D32_epitope_0.pdb
    ├── 3D32_epitope_0.trb
    └── ...
```

Use `--output-dir` to specify a custom output directory.

## Environment

Scripts use the RFpeptides environment at `../env_rfpeptides`. Ensure it's properly set up:

```bash
mamba run -p ./env_rfpeptides python -c "from rfdiffusion.inference import utils; print('OK')"
```
