#!/usr/bin/env python
"""Run peptide binder design against a target protein.

This script covers Use Cases 1, 2, and 4 from the RFpeptides paper:
- Case 1: Diverse binding sites (MCL1, MDM2, GABARAP)
- Case 2: AI-predicted structures (RbtA)
- Case 4: Rapid discovery (high-throughput generation)

Supports both linear (default) and cyclic peptide binders.

Usage:
    python run_binder_design.py --target mcl1 --num-designs 50
    python run_binder_design.py --target mcl1 --num-designs 50 --cyclic
    python run_binder_design.py --pdb /path/to/target.pdb --chain A --num-designs 100
"""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
MCP_ROOT = SCRIPT_DIR.parent

from rfpeptides_core import design_binder

# Default output directory
DEFAULT_OUTPUT_DIR = MCP_ROOT / "results" / "binder_outputs"


# Predefined targets with optimal parameters
TARGETS = {
    "mcl1": {
        "pdb": "examples/structures/targets/2PQK.pdb",
        "chain": "A",
        "residue_range": (203, 321),  # Main domain (gap at 198-202 in PDB)
        "binder_length": (12, 16),
        "description": "MCL1 - Concave helical BH3-binding groove",
    },
    "mdm2": {
        "pdb": "examples/structures/targets/4HFZ.pdb",
        "chain": "A",
        "residue_range": (26, 108),  # Actual residue numbering in PDB
        "binder_length": (16, 18),
        "description": "MDM2 - Concave helical p53-binding pocket",
    },
    "gabarap": {
        "pdb": "examples/structures/targets/3D32.pdb",
        "chain": "A",
        "residue_range": (1, 118),  # Actual residue numbering in PDB
        "binder_length": (13, 18),
        "description": "GABARAP - Mixed alpha/beta LIR-docking site",
    },
    "rbta": {
        "pdb": "examples/structures/targets/9CDV.pdb",
        "chain": "A",
        "residue_range": (2, 406),  # Main domain (gap at 407-410 in PDB)
        "binder_length": (14, 18),
        "description": "RbtA - Flat surface (AI-predicted structure)",
    },
}


def main():
    parser = argparse.ArgumentParser(
        description="Run peptide binder design (linear or cyclic)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Design linear binders for MCL1 (predefined target)
    python run_binder_design.py --target mcl1 --num-designs 50

    # Design cyclic binders for MCL1
    python run_binder_design.py --target mcl1 --num-designs 50 --cyclic

    # Design binders for custom PDB
    python run_binder_design.py --pdb target.pdb --chain A --binder-length 12 16 --num-designs 100

    # Design cyclic binders with custom output directory
    python run_binder_design.py --target gabarap --num-designs 20 --cyclic --output-dir ./my_outputs

    # List available predefined targets
    python run_binder_design.py --list-targets
        """,
    )

    parser.add_argument(
        "--target",
        choices=list(TARGETS.keys()),
        help="Predefined target name",
    )
    parser.add_argument(
        "--pdb",
        type=str,
        help="Path to custom target PDB file",
    )
    parser.add_argument(
        "--chain",
        type=str,
        default="A",
        help="Target chain ID (default: A)",
    )
    parser.add_argument(
        "--residue-range",
        type=int,
        nargs=2,
        metavar=("START", "END"),
        help="Target residue range (default: auto-detect)",
    )
    parser.add_argument(
        "--binder-length",
        type=int,
        nargs=2,
        default=[12, 16],
        metavar=("MIN", "MAX"),
        help="Binder length range (default: 12-16)",
    )
    parser.add_argument(
        "--num-designs",
        type=int,
        default=50,
        help="Number of designs to generate (default: 50)",
    )
    parser.add_argument(
        "--diffusion-steps",
        type=int,
        default=50,
        help="Number of diffusion timesteps (default: 50)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--device",
        type=int,
        default=None,
        metavar="ID",
        help="CUDA device ID (e.g., 0, 1, 2). If not specified, uses default GPU.",
    )
    parser.add_argument(
        "--cyclic",
        action="store_true",
        default=False,
        help="Generate cyclic peptide binders (default: linear binders)",
    )
    parser.add_argument(
        "--list-targets",
        action="store_true",
        help="List available predefined targets",
    )

    args = parser.parse_args()

    # List targets mode
    if args.list_targets:
        print("Available predefined targets:")
        print("-" * 60)
        for name, info in TARGETS.items():
            print(f"  {name:12} - {info['description']}")
            print(f"               PDB: {info['pdb']}")
            print(f"               Length: {info['binder_length'][0]}-{info['binder_length'][1]} residues")
            print()
        return

    # Validate inputs
    if not args.target and not args.pdb:
        parser.error("Either --target or --pdb must be specified")

    # Get parameters
    if args.target:
        target_info = TARGETS[args.target]
        pdb_path = str(MCP_ROOT / target_info["pdb"])
        chain = target_info["chain"]
        residue_range = target_info["residue_range"]
        binder_length = target_info["binder_length"]
    else:
        pdb_path = args.pdb
        chain = args.chain
        residue_range = tuple(args.residue_range) if args.residue_range else None
        binder_length = tuple(args.binder_length)

    # Run directly (no job queue)
    binder_type = "cyclic" if args.cyclic else "linear"
    print(f"Running {binder_type} binder design...")
    print(f"  Target: {pdb_path}")
    print(f"  Chain: {chain}")
    print(f"  Binder length: {binder_length[0]}-{binder_length[1]} residues")
    print(f"  Cyclic: {args.cyclic}")
    print(f"  Num designs: {args.num_designs}")
    print(f"  Output dir: {args.output_dir}")
    print(f"  Device: {args.device if args.device is not None else 'default'}")
    print()

    try:
        result = design_binder(
            target_pdb=pdb_path,
            binder_length=binder_length,
            num_designs=args.num_designs,
            output_dir=args.output_dir,
            target_chain=chain,
            target_residue_range=residue_range,
            diffusion_steps=args.diffusion_steps,
            device=args.device,
            cyclic=args.cyclic,
        )

        print(f"Design completed successfully!")
        print(f"Generated {result.num_generated} designs")
        print(f"Output directory: {result.output_dir}")
        print()
        print("PDB files:")
        for pdb in result.pdb_files[:10]:  # Show first 10
            print(f"  {pdb}")
        if len(result.pdb_files) > 10:
            print(f"  ... and {len(result.pdb_files) - 10} more")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
