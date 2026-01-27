#!/usr/bin/env python
"""Run unconditional cyclic peptide backbone enumeration.

This script covers Use Case 6 from the RFpeptides paper:
- Structural space enumeration without a target
- Generate diverse cyclic peptide backbone conformations
- Explore the macrocyclic structural landscape

Usage:
    python run_backbone_enumeration.py --length 10 --num-designs 100
    python run_backbone_enumeration.py --length 8 12 --num-designs 1000
"""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
MCP_ROOT = SCRIPT_DIR.parent

from rfpeptides_core import generate_cyclic_backbone

# Default output directory
DEFAULT_OUTPUT_DIR = MCP_ROOT / "results" / "backbone_outputs"


def main():
    parser = argparse.ArgumentParser(
        description="Run unconditional cyclic peptide backbone enumeration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate 100 10-mer cyclic backbones
    python run_backbone_enumeration.py --length 10 --num-designs 100

    # Generate variable-length backbones (8-12 residues)
    python run_backbone_enumeration.py --length 8 12 --num-designs 500

    # High-quality generation with more diffusion steps
    python run_backbone_enumeration.py --length 10 --num-designs 50 --diffusion-steps 100

    # Custom output directory
    python run_backbone_enumeration.py --length 10 --num-designs 50 --output-dir ./my_outputs

Recommended Parameters:
    - For quick exploration: 50-100 designs, 50 diffusion steps
    - For comprehensive enumeration: 1000-10000 designs
    - Typical lengths: 7-16 residues (tested in paper)
        """,
    )

    parser.add_argument(
        "--length",
        type=int,
        nargs="+",
        required=True,
        metavar="N",
        help="Peptide length (single value) or range (min max)",
    )
    parser.add_argument(
        "--num-designs",
        type=int,
        default=100,
        help="Number of designs to generate (default: 100)",
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

    args = parser.parse_args()

    # Parse length
    if len(args.length) == 1:
        min_len = max_len = args.length[0]
    elif len(args.length) == 2:
        min_len, max_len = args.length
    else:
        parser.error("--length must be 1 or 2 values")

    if min_len > max_len:
        parser.error("Min length cannot be greater than max length")

    if min_len < 5 or max_len > 30:
        print("Warning: Lengths outside 7-16 residues may have lower success rates")

    # Determine peptide length parameter
    if min_len == max_len:
        peptide_length = min_len
    else:
        peptide_length = (min_len, max_len)

    # Run directly (no job queue)
    print(f"Running backbone enumeration...")
    print(f"  Length: {min_len}-{max_len} residues")
    print(f"  Num designs: {args.num_designs}")
    print(f"  Diffusion steps: {args.diffusion_steps}")
    print(f"  Output dir: {args.output_dir}")
    print(f"  Device: {args.device if args.device is not None else 'default'}")
    print()

    try:
        result = generate_cyclic_backbone(
            peptide_length=peptide_length,
            num_designs=args.num_designs,
            output_dir=args.output_dir,
            diffusion_steps=args.diffusion_steps,
            device=args.device,
        )

        print(f"Generation completed successfully!")
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
