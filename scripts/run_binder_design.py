#!/usr/bin/env python
"""Run cyclic peptide binder design against a target protein.

This script covers Use Cases 1, 2, and 4 from the RFpeptides paper:
- Case 1: Diverse binding sites (MCL1, MDM2, GABARAP)
- Case 2: AI-predicted structures (RbtA)
- Case 4: Rapid discovery (high-throughput generation)

Usage:
    python run_binder_design.py --target mcl1 --num-designs 50
    python run_binder_design.py --pdb /path/to/target.pdb --chain A --num-designs 100
"""

import argparse
import sys
from pathlib import Path

# Add src to path
SCRIPT_DIR = Path(__file__).parent.resolve()
MCP_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(MCP_ROOT))

from src.jobs.manager import job_manager


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
        description="Run cyclic peptide binder design",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Design binders for MCL1 (predefined target)
    python run_binder_design.py --target mcl1 --num-designs 50

    # Design binders for custom PDB
    python run_binder_design.py --pdb target.pdb --chain A --binder-length 12 16 --num-designs 100

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
        "--job-name",
        type=str,
        help="Custom job name",
    )
    parser.add_argument(
        "--list-targets",
        action="store_true",
        help="List available predefined targets",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for job to complete before exiting",
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
        job_name = args.job_name or f"binder_{args.target}"
    else:
        pdb_path = args.pdb
        chain = args.chain
        residue_range = tuple(args.residue_range) if args.residue_range else None
        binder_length = tuple(args.binder_length)
        job_name = args.job_name or f"binder_{Path(pdb_path).stem}"

    # Build config
    if residue_range:
        contigs = f"{chain}{residue_range[0]}-{residue_range[1]}/0 {binder_length[0]}-{binder_length[1]}"
    else:
        # Auto-detect from PDB
        from src.rfpeptides_core import _get_chain_residue_range
        start, end = _get_chain_residue_range(pdb_path, chain)
        contigs = f"{chain}{start}-{end}/0 {binder_length[0]}-{binder_length[1]}"

    config = {
        "output_prefix": f"{Path(pdb_path).stem}_binder",
        "num_designs": args.num_designs,
        "input_pdb": pdb_path,
        "contigs": contigs,
        "cyclic": True,
        "cyc_chains": "B",
        "diffusion_steps": args.diffusion_steps,
    }

    # Submit job
    print(f"Submitting binder design job...")
    print(f"  Target: {pdb_path}")
    print(f"  Chain: {chain}")
    print(f"  Binder length: {binder_length[0]}-{binder_length[1]} residues")
    print(f"  Num designs: {args.num_designs}")
    print()

    result = job_manager.submit_job(config=config, job_name=job_name)

    print(f"Job submitted: {result['job_id']}")
    print(f"Queue position: {result['queue_position']}")

    if args.wait:
        import time
        print()
        print("Waiting for job to complete...")
        job_id = result['job_id']
        while True:
            status = job_manager.get_job_status(job_id)
            if status['status'] in ['completed', 'failed', 'cancelled']:
                break
            time.sleep(5)

        print()
        if status['status'] == 'completed':
            result_info = job_manager.get_job_result(job_id)
            print(f"Job completed successfully!")
            print(f"Output files ({result_info.get('num_generated', 0)} designs):")
            for pdb in result_info.get('pdb_files', []):
                print(f"  {pdb}")
        else:
            print(f"Job {status['status']}: {status.get('error', 'Unknown error')}")
    else:
        print()
        print(f"Check status: python scripts/manage_jobs.py status {result['job_id']}")


if __name__ == "__main__":
    main()
