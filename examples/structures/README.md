# RFpeptides Example Structures

This directory contains PDB structures used for cyclic peptide binder design examples.

## Directory Structure

```
structures/
├── targets/      # Target proteins for binder design
├── complexes/    # Experimentally validated peptide-protein complexes
└── benchmarks/   # Natural cyclic peptide benchmarks for validation
```

## Target Structures

| PDB | Protein | Pocket Type | Use Case |
|-----|---------|-------------|----------|
| 2PQK | MCL1 | Concave helical groove | BH3 mimetics |
| 4HFZ | MDM2 | Concave helical pocket | p53 inhibitors |
| 3D32 | GABARAP | Mixed alpha/beta site | Autophagy modulators |
| 9CDV | RbtA | Flat surface | AI-predicted target |

## Complex Structures (X-ray Validated)

| PDB | Complex | Resolution | Notes |
|-----|---------|------------|-------|
| 9CDT | MCB_D2:MCL1 | 2.1 Å | Designed cyclic peptide bound to MCL1 |
| 9CDU | RBB_D10:RbtA | 2.6 Å | Designed cyclic peptide bound to RbtA |
| 9HGC | GAB_D8:GABARAPL1 | - | Designed peptide in GABARAPL1 complex |
| 9HGD | GAB_D23:GABARAP | 1.5 Å | High-resolution GABARAP complex |

## Natural Cyclic Peptide Benchmarks

| PDB | Description | Length |
|-----|-------------|--------|
| 1JBL | Natural cyclic peptide | 10 residues |
| 2MW0 | Natural cyclic peptide | 8 residues |
| 2LWV | Natural cyclic peptide | 9 residues |
| 5KX1 | Natural cyclic peptide | Variable |

## Usage

These structures are used by the scripts in `../scripts/`:

```bash
# Design binders for MCL1
python scripts/run_binder_design.py --target mcl1 --num-designs 50

# Design binders with custom PDB
python scripts/run_binder_design.py --pdb examples/structures/targets/2PQK.pdb --num-designs 50
```
