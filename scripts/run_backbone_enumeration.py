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

# Add src to path
SCRIPT_DIR = Path(__file__).parent.resolve()
MCP_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(MCP_ROOT))

from src.jobs.manager import job_manager


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
        "--job-name",
        type=str,
        help="Custom job name",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for job to complete before exiting",
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

    # Build config
    job_name = args.job_name or f"backbone_{min_len}mer"
    if min_len != max_len:
        job_name = args.job_name or f"backbone_{min_len}-{max_len}mer"

    config = {
        "output_prefix": f"cyclic_{min_len}mer",
        "num_designs": args.num_designs,
        "contigs": f"{min_len}-{max_len}",
        "cyclic": True,
        "cyc_chains": "a",  # lowercase = self-cyclic
        "diffusion_steps": args.diffusion_steps,
    }

    # Submit job
    print(f"Submitting backbone enumeration job...")
    print(f"  Length: {min_len}-{max_len} residues")
    print(f"  Num designs: {args.num_designs}")
    print(f"  Diffusion steps: {args.diffusion_steps}")
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
