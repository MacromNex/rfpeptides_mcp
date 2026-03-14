"""RFdiffusion execution wrapper.

This module handles the execution of RFdiffusion commands and parsing of outputs.
"""

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# Resolve paths relative to this file's location
_MODULE_DIR = Path(__file__).parent.absolute()
_MCP_ROOT = _MODULE_DIR.parent

# RFdiffusion directory - can be overridden via environment variable (e.g., in Docker)
_RFDIFF_DIR = Path(os.environ.get("RFPEPTIDES_RFDIFF_DIR", str(_MCP_ROOT / "repo" / "rfd_macro")))
_ENV_PATH = _MCP_ROOT / "env_rfpeptides"

# Default mamba path - can be overridden via environment variable
_DEFAULT_MAMBA = "/home/xux/miniforge3/bin/mamba"
MAMBA_PATH = os.environ.get("RFPEPTIDES_MAMBA_PATH", _DEFAULT_MAMBA)

# Docker mode: skip mamba if not available
_USE_MAMBA = Path(MAMBA_PATH).exists() and _ENV_PATH.exists()


@dataclass
class RFDiffusionConfig:
    """Configuration for an RFdiffusion run.

    Attributes:
        output_prefix: Path prefix for output files (without extension).
        num_designs: Number of designs to generate.
        contigs: Contig specification string (e.g., "12-16 A1-180/0").
        cyclic: Whether to generate cyclic peptides.
        cyc_chains: Chain(s) to make cyclic ('a' for self-cyclic binder).
        diffusion_steps: Number of diffusion timesteps.
        input_pdb: Optional path to input/target PDB file.
        hotspot_res: Optional hotspot residue string (e.g., "A46,A48,A49").
        config_name: Hydra config name (default: "base").
        device: CUDA device ID (e.g., 0, 1, 2). If None, uses default GPU.
    """
    output_prefix: str
    num_designs: int
    contigs: str
    cyclic: bool = True
    cyc_chains: str = "a"
    diffusion_steps: int = 50
    input_pdb: Optional[str] = None
    hotspot_res: Optional[str] = None
    config_name: str = "base"
    device: Optional[int] = None


def build_command(config: RFDiffusionConfig) -> list[str]:
    """Build the RFdiffusion command from configuration.

    Args:
        config: RFDiffusionConfig instance with run parameters.

    Returns:
        List of command arguments for subprocess execution.
    """
    if _USE_MAMBA:
        cmd = [MAMBA_PATH, "run", "-p", str(_ENV_PATH), "python"]
    else:
        cmd = ["python"]
    cmd += [
        "scripts/run_inference.py",
        f"--config-name={config.config_name}",
        f"inference.output_prefix={config.output_prefix}",
        f"inference.num_designs={config.num_designs}",
        f"contigmap.contigs=[{config.contigs}]",
        f"inference.cyclic={config.cyclic}",
        f"inference.cyc_chains={config.cyc_chains!r}",
        f"diffuser.T={config.diffusion_steps}",
    ]

    if config.input_pdb:
        cmd.append(f"inference.input_pdb={config.input_pdb}")

    if config.hotspot_res:
        cmd.append(f"ppi.hotspot_res=[{config.hotspot_res}]")

    return cmd


def run_rfdiffusion(config: RFDiffusionConfig, output_dir: str) -> "GenerationResult":
    """Execute RFdiffusion and return results.

    Args:
        config: RFDiffusionConfig instance with run parameters.
        output_dir: Directory to save outputs.

    Returns:
        GenerationResult with paths to generated files.

    Raises:
        RuntimeError: If RFdiffusion execution fails.
        FileNotFoundError: If RFdiffusion directory or environment not found.
    """
    # Import here to avoid circular dependency
    from .rfpeptides_core import GenerationResult

    # Validate paths
    if not _RFDIFF_DIR.exists():
        raise FileNotFoundError(
            f"RFdiffusion directory not found: {_RFDIFF_DIR}\n"
            "Set RFPEPTIDES_RFDIFF_DIR or ensure repo is properly linked."
        )

    if _USE_MAMBA and not _ENV_PATH.exists():
        raise FileNotFoundError(
            f"RFpeptides environment not found: {_ENV_PATH}\n"
            "Please create the conda environment first."
        )

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Build command
    cmd = build_command(config)
    cmd_str = " ".join(cmd)

    # Set up environment with CUDA device selection
    env = os.environ.copy()
    if config.device is not None:
        env["CUDA_VISIBLE_DEVICES"] = str(config.device)
        cmd_str = f"CUDA_VISIBLE_DEVICES={config.device} " + cmd_str

    # Execute from RFdiffusion directory
    try:
        result = subprocess.run(
            cmd,
            cwd=str(_RFDIFF_DIR),
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"RFdiffusion execution failed:\n"
            f"Command: {cmd_str}\n"
            f"Return code: {e.returncode}\n"
            f"Stdout: {e.stdout}\n"
            f"Stderr: {e.stderr}"
        )

    # Collect output files
    pdb_files = sorted(output_path.glob(f"{Path(config.output_prefix).name}*.pdb"))
    trb_files = sorted(output_path.glob(f"{Path(config.output_prefix).name}*.trb"))

    return GenerationResult(
        pdb_files=pdb_files,
        trb_files=trb_files,
        output_dir=output_path,
        num_generated=len(pdb_files),
        command=cmd_str,
    )


def get_rfdiffusion_info() -> dict:
    """Get information about the RFdiffusion installation.

    Returns:
        Dictionary with installation details.
    """
    return {
        "rfdiffusion_dir": str(_RFDIFF_DIR),
        "environment_path": str(_ENV_PATH),
        "mamba_path": MAMBA_PATH,
        "rfdiffusion_exists": _RFDIFF_DIR.exists(),
        "environment_exists": _ENV_PATH.exists(),
    }
