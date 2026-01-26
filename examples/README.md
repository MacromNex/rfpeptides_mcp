# RFpeptides Examples

Example data and structures for the RFpeptides cyclic peptide design pipeline.

## Directory Structure

```
examples/
├── structures/           # PDB structure files
│   ├── targets/         # Target proteins for binder design
│   ├── complexes/       # Experimentally validated complexes
│   └── benchmarks/      # Natural cyclic peptide benchmarks
└── README.md
```

## Use Cases

RFpeptides supports six core use cases:

| # | Use Case | Description | Script |
|---|----------|-------------|--------|
| 1 | Diverse Binding Sites | Design for different pocket types | `run_binder_design.py` |
| 2 | AI-Predicted Structures | Use AF2/RF2 predicted targets | `run_binder_design.py` |
| 3 | Epitope-Specific | Target specific residues with hotspots | `run_epitope_design.py` |
| 4 | Rapid Discovery | High-throughput generation | `run_binder_design.py` |
| 5 | Atomic Accuracy | Validate against X-ray structures | N/A (validation) |
| 6 | Structural Enumeration | Explore macrocyclic space | `run_backbone_enumeration.py` |

## Quick Start

### Design Binders for MCL1

```bash
cd /path/to/rfpeptides_mcp
python scripts/run_binder_design.py --target mcl1 --num-designs 50
```

### Design Epitope-Specific Binders for GABARAP

```bash
python scripts/run_epitope_design.py --target gabarap --num-designs 50
```

### Generate Cyclic Peptide Backbones

```bash
python scripts/run_backbone_enumeration.py --length 10 --num-designs 100
```

## Available Targets

### For Binder Design

| Target | PDB | Description |
|--------|-----|-------------|
| `mcl1` | 2PQK | Anti-apoptotic protein, BH3-binding groove |
| `mdm2` | 4HFZ | p53 regulator, helical binding pocket |
| `gabarap` | 3D32 | Autophagy receptor, LIR-docking site |
| `rbta` | 9CDV | AI-predicted structure, flat surface |

### For Hotspot-Guided Design

| Target | Hotspots | Description |
|--------|----------|-------------|
| `gabarap` | K46, K48, Y49, L50, F60, L63 | LIR-docking site |
| `mcl1` | M231, F228, L267, L270, G271, V274 | BH3-binding groove |
| `rbta` | Custom | Surface epitope |

## References

- RFpeptides paper: De novo macrocyclic peptide design using RFdiffusion
- RFdiffusion: https://github.com/RosettaCommons/RFdiffusion
