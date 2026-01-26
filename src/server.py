"""FastMCP server for RFpeptides cyclic peptide backbone generation.

This module exposes the three core RFpeptides functions as MCP tools:
- generate_cyclic_backbone: Unconditional cyclic peptide generation
- design_cyclic_binder: Cyclic binder design against a target
- design_cyclic_binder_with_hotspots: Epitope-specific binder design

All long-running tasks use async job submission with FIFO queue management.
"""

import sys
from pathlib import Path
from typing import Annotated, Optional

# Add src directory to path for standalone execution (fastmcp run)
_src_dir = Path(__file__).parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from fastmcp import FastMCP

from rfpeptides_core import _parse_length, _get_chain_residue_range
from runner import get_rfdiffusion_info
from jobs.manager import job_manager

# Create the MCP server
mcp = FastMCP(
    "RFpeptides",
    instructions=(
        "Cyclic peptide backbone generation using RFdiffusion. "
        "Provides three core functions: unconditional cyclic backbone generation, "
        "cyclic binder design, and epitope-specific binder design with hotspots. "
        "All long-running tasks use async job submission with FIFO queue management."
    ),
)


# ==============================================================================
# Job Management Tools
# ==============================================================================

@mcp.tool()
def get_job_status(job_id: str) -> dict:
    """
    Get the status of a submitted RFpeptides backbone generation job.

    Args:
        job_id: The job ID returned from a submit_* function

    Returns:
        Dictionary with job status, timestamps, queue position (if pending), and any errors
    """
    return job_manager.get_job_status(job_id)


@mcp.tool()
def get_job_result(job_id: str) -> dict:
    """
    Get the results of a completed RFpeptides job.

    Args:
        job_id: The job ID of a completed job

    Returns:
        Dictionary with output file paths and job results
    """
    return job_manager.get_job_result(job_id)


@mcp.tool()
def get_job_log(job_id: str, tail: int = 50) -> dict:
    """
    Get log output from a running or completed job.

    Args:
        job_id: The job ID to get logs for
        tail: Number of lines from end (default: 50, use 0 for all)

    Returns:
        Dictionary with log lines and total line count
    """
    return job_manager.get_job_log(job_id, tail)


@mcp.tool()
def cancel_job(job_id: str) -> dict:
    """
    Cancel a pending or running RFpeptides job.

    Args:
        job_id: The job ID to cancel

    Returns:
        Success or error message
    """
    return job_manager.cancel_job(job_id)


@mcp.tool()
def list_jobs(status: Optional[str] = None) -> dict:
    """
    List all submitted RFpeptides jobs.

    Args:
        status: Filter by status (pending, running, completed, failed, cancelled)

    Returns:
        List of jobs with their status
    """
    return job_manager.list_jobs(status)


@mcp.tool()
def get_queue_info() -> dict:
    """
    Get current job queue status.

    Returns:
        Dictionary with queue size, current running job, and job counts by status
    """
    return job_manager.get_queue_info()


@mcp.tool()
def resubmit_job(job_id: str) -> dict:
    """
    Resubmit a failed or cancelled job.

    Creates a new job with the same parameters as the original.
    Useful for retrying jobs that failed due to server restarts or transient errors.

    Args:
        job_id: The job ID of the failed/cancelled job to resubmit

    Returns:
        Dictionary with new job_id and queue position, or error if job cannot be resubmitted
    """
    return job_manager.resubmit_job(job_id)


# ==============================================================================
# Backbone Generation Tools
# ==============================================================================

@mcp.tool()
def submit_cyclic_backbone(
    peptide_length: Annotated[
        int,
        "Length of the cyclic peptide in residues (typically 7-20)"
    ],
    num_designs: Annotated[
        int,
        "Number of backbone designs to generate"
    ],
    peptide_length_max: Annotated[
        Optional[int],
        "Maximum peptide length for variable-length generation (if different from peptide_length)"
    ] = None,
    diffusion_steps: Annotated[
        int,
        "Number of diffusion timesteps (higher = more diverse, default: 50)"
    ] = 50,
    job_name: Annotated[
        Optional[str],
        "Optional name for job tracking"
    ] = None,
) -> dict:
    """Submit an unconditional cyclic peptide backbone generation job.

    This function generates diverse cyclic peptide backbone structures without
    any target protein, useful for exploring the structural landscape of
    macrocycles (Use Case 6: Structural Space Enumeration).

    The generated backbones can subsequently be:
    1. Designed with sequences using LigandMPNN
    2. Validated with structure prediction (AfCycDesign)
    3. Clustered to identify unique structural families

    Args:
        peptide_length: Minimum/fixed length of the cyclic peptide
        num_designs: Number of backbone designs to generate
        peptide_length_max: Maximum length for variable-length generation
        diffusion_steps: Number of diffusion timesteps (default: 50)
        job_name: Optional name for job tracking

    Returns:
        Dictionary with job_id for tracking. Use:
        - get_job_status(job_id) to check progress
        - get_job_result(job_id) to get output files when completed
        - get_job_log(job_id) to see execution logs
    """
    min_len = peptide_length
    max_len = peptide_length_max if peptide_length_max else peptide_length

    config = {
        "output_prefix": f"cyclic_{min_len}mer",
        "num_designs": num_designs,
        "contigs": f"{min_len}-{max_len}",
        "cyclic": True,
        "cyc_chains": "a",  # lowercase = self-cyclic
        "diffusion_steps": diffusion_steps,
    }

    return job_manager.submit_job(
        config=config,
        job_name=job_name or f"cyclic_backbone_{min_len}mer"
    )


@mcp.tool()
def submit_cyclic_binder(
    target_pdb: Annotated[
        str,
        "Path to the target protein PDB file"
    ],
    binder_length: Annotated[
        int,
        "Minimum length of the binder peptide in residues (typically 12-18)"
    ],
    num_designs: Annotated[
        int,
        "Number of binder designs to generate"
    ],
    binder_length_max: Annotated[
        Optional[int],
        "Maximum binder length for variable-length generation"
    ] = None,
    target_chain: Annotated[
        str,
        "Chain ID of the target protein (default: 'A')"
    ] = "A",
    target_start_residue: Annotated[
        Optional[int],
        "Start residue number of target to include"
    ] = None,
    target_end_residue: Annotated[
        Optional[int],
        "End residue number of target to include"
    ] = None,
    diffusion_steps: Annotated[
        int,
        "Number of diffusion timesteps (default: 50)"
    ] = 50,
    job_name: Annotated[
        Optional[str],
        "Optional name for job tracking"
    ] = None,
) -> dict:
    """Submit a cyclic peptide binder design job against a target protein.

    This function designs cyclic peptide backbones that bind to a target protein
    structure without specific hotspot constraints (Use Cases 1a, 1c, 4).

    The diffusion process generates binders that complement the target surface,
    exploring diverse binding modes and topologies.

    Args:
        target_pdb: Path to the target protein PDB file
        binder_length: Minimum length of the binder peptide
        num_designs: Number of binder designs to generate
        binder_length_max: Maximum binder length for variable-length generation
        target_chain: Chain ID of the target protein (default: 'A')
        target_start_residue: Start residue number of target to include
        target_end_residue: End residue number of target to include
        diffusion_steps: Number of diffusion timesteps (default: 50)
        job_name: Optional name for job tracking

    Returns:
        Dictionary with job_id for tracking
    """
    min_len = binder_length
    max_len = binder_length_max if binder_length_max else binder_length
    target_path = Path(target_pdb)

    # Determine residue range
    if target_start_residue is not None and target_end_residue is not None:
        start, end = target_start_residue, target_end_residue
    else:
        start, end = _get_chain_residue_range(target_pdb, target_chain)

    contigs = f"{target_chain}{start}-{end}/0 {min_len}-{max_len}"
    output_prefix = target_path.stem + "_binder"

    config = {
        "output_prefix": output_prefix,
        "num_designs": num_designs,
        "input_pdb": str(target_pdb),
        "contigs": contigs,
        "cyclic": True,
        "cyc_chains": "B",  # uppercase = binder chain
        "diffusion_steps": diffusion_steps,
    }

    return job_manager.submit_job(
        config=config,
        job_name=job_name or f"binder_{target_path.stem}"
    )


@mcp.tool()
def submit_cyclic_binder_with_hotspots(
    target_pdb: Annotated[
        str,
        "Path to the target protein PDB file"
    ],
    hotspot_residues: Annotated[
        list[int],
        "List of residue numbers on the target to specifically target"
    ],
    binder_length: Annotated[
        int,
        "Minimum length of the binder peptide in residues"
    ],
    num_designs: Annotated[
        int,
        "Number of binder designs to generate"
    ],
    binder_length_max: Annotated[
        Optional[int],
        "Maximum binder length for variable-length generation"
    ] = None,
    target_chain: Annotated[
        str,
        "Chain ID of the target protein (default: 'A')"
    ] = "A",
    target_start_residue: Annotated[
        Optional[int],
        "Start residue number of target to include"
    ] = None,
    target_end_residue: Annotated[
        Optional[int],
        "End residue number of target to include"
    ] = None,
    diffusion_steps: Annotated[
        int,
        "Number of diffusion timesteps (default: 50)"
    ] = 50,
    job_name: Annotated[
        Optional[str],
        "Optional name for job tracking"
    ] = None,
) -> dict:
    """Submit a cyclic peptide binder design job with epitope-specific hotspot targeting.

    This function designs cyclic peptide backbones that specifically interact
    with designated hotspot residues on the target protein (Use Cases 1b, 2, 3a, 3b).

    Hotspot guidance steers the diffusion to generate binders contacting the
    specified residues, useful for:
    - Targeting specific epitopes for immunological applications
    - Designing competitive inhibitors of protein-protein interactions
    - Focusing binding on functionally important residues

    Args:
        target_pdb: Path to the target protein PDB file
        hotspot_residues: List of residue numbers on the target to specifically target
        binder_length: Minimum length of the binder peptide
        num_designs: Number of binder designs to generate
        binder_length_max: Maximum binder length for variable-length generation
        target_chain: Chain ID of the target protein (default: 'A')
        target_start_residue: Start residue number of target to include
        target_end_residue: End residue number of target to include
        diffusion_steps: Number of diffusion timesteps (default: 50)
        job_name: Optional name for job tracking

    Returns:
        Dictionary with job_id for tracking
    """
    min_len = binder_length
    max_len = binder_length_max if binder_length_max else binder_length
    target_path = Path(target_pdb)

    # Determine residue range
    if target_start_residue is not None and target_end_residue is not None:
        start, end = target_start_residue, target_end_residue
    else:
        start, end = _get_chain_residue_range(target_pdb, target_chain)

    contigs = f"{target_chain}{start}-{end}/0 {min_len}-{max_len}"

    # Format hotspot residues: A46,A48,A49,...
    hotspot_str = ",".join(f"{target_chain}{res}" for res in hotspot_residues)

    output_prefix = target_path.stem + "_epitope"

    config = {
        "output_prefix": output_prefix,
        "num_designs": num_designs,
        "input_pdb": str(target_pdb),
        "contigs": contigs,
        "cyclic": True,
        "cyc_chains": "B",
        "diffusion_steps": diffusion_steps,
        "hotspot_res": hotspot_str,
    }

    return job_manager.submit_job(
        config=config,
        job_name=job_name or f"epitope_{target_path.stem}"
    )


# ==============================================================================
# Utility Tools
# ==============================================================================

@mcp.tool()
def validate_pdb_file(file_path: str) -> dict:
    """
    Validate a PDB file structure.

    Args:
        file_path: Path to PDB file to validate

    Returns:
        Dictionary with validation results and structural information
    """
    try:
        pdb_path = Path(file_path)
        if not pdb_path.exists():
            return {"status": "error", "error": f"File not found: {file_path}"}

        if not pdb_path.is_file():
            return {"status": "error", "error": f"Not a file: {file_path}"}

        if pdb_path.stat().st_size == 0:
            return {"status": "error", "error": f"Empty file: {file_path}"}

        # Basic PDB validation
        chains = set()
        residues = {}
        atom_count = 0

        with open(pdb_path, 'r') as f:
            for line in f:
                if line.startswith('ATOM') or line.startswith('HETATM'):
                    atom_count += 1
                    chain = line[21:22].strip() or "_"
                    res_num = line[22:26].strip()
                    chains.add(chain)
                    if chain not in residues:
                        residues[chain] = set()
                    residues[chain].add(res_num)

        chain_info = {ch: len(res) for ch, res in residues.items()}

        return {
            "status": "success",
            "file_path": str(pdb_path),
            "file_size_bytes": pdb_path.stat().st_size,
            "chains": list(chains),
            "residues_per_chain": chain_info,
            "total_residues": sum(chain_info.values()),
            "atom_count": atom_count,
            "valid_pdb": atom_count > 0
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
def get_server_info() -> dict:
    """
    Get information about the RFpeptides MCP server.

    Returns:
        Dictionary with server information, installation paths, and available tools
    """
    info = get_rfdiffusion_info()

    return {
        "status": "success",
        "server_name": "RFpeptides",
        "version": "1.0.0",
        "description": "Cyclic peptide backbone generation using RFdiffusion",
        "reference": "Watson et al., De novo design of protein structure and function with RFdiffusion",
        "rfdiffusion_dir": info["rfdiffusion_dir"],
        "environment_path": info["environment_path"],
        "jobs_directory": str(job_manager.jobs_dir),
        "rfdiffusion_exists": info["rfdiffusion_exists"],
        "environment_exists": info["environment_exists"],
        "available_tools": {
            "backbone_generation": [
                {
                    "name": "submit_cyclic_backbone",
                    "description": "Generate unconditional cyclic peptide backbones"
                },
                {
                    "name": "submit_cyclic_binder",
                    "description": "Design cyclic binders against a target protein"
                },
                {
                    "name": "submit_cyclic_binder_with_hotspots",
                    "description": "Design cyclic binders with epitope-specific targeting"
                }
            ],
            "job_management": [
                "get_job_status",
                "get_job_result",
                "get_job_log",
                "cancel_job",
                "list_jobs",
                "get_queue_info",
                "resubmit_job"
            ],
            "utilities": [
                "validate_pdb_file",
                "get_server_info"
            ]
        },
        "job_queue": "FIFO (one job at a time due to GPU constraints)"
    }


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
