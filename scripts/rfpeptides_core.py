"""Standalone RFpeptides backbone generation functions for local testing.

This module provides three core functions for cyclic peptide backbone generation
using RFdiffusion. It is self-contained and does not depend on the src/ directory.

Functions:
    generate_cyclic_backbone: Unconditional cyclic peptide backbone generation
    design_cyclic_binder: Design cyclic peptide binders against a target protein
    design_cyclic_binder_with_hotspots: Design with epitope-specific targeting
"""

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union, Optional


# Resolve paths relative to this file's location
_SCRIPT_DIR = Path(__file__).parent.absolute()
_MCP_ROOT = _SCRIPT_DIR.parent
_RFDIFF_DIR = _MCP_ROOT / "repo" / "rfd_macro"
_ENV_PATH = _MCP_ROOT / "env_rfpeptides"

# Default mamba path - can be overridden via environment variable
_DEFAULT_MAMBA = "/home/xux/miniforge3/bin/mamba"
MAMBA_PATH = os.environ.get("RFPEPTIDES_MAMBA_PATH", _DEFAULT_MAMBA)


@dataclass
class GenerationResult:
    """Result from backbone generation.

    Attributes:
        pdb_files: List of generated PDB structure files.
        trb_files: List of corresponding .trb trajectory/metadata files.
        output_dir: Directory containing all outputs.
        num_generated: Number of designs successfully generated.
        command: The RFdiffusion command that was executed.
    """
    pdb_files: list[Path] = field(default_factory=list)
    trb_files: list[Path] = field(default_factory=list)
    output_dir: Path = field(default_factory=Path)
    num_generated: int = 0
    command: str = ""


@dataclass
class RFDiffusionConfig:
    """Configuration for an RFdiffusion run.

    Attributes:
        output_prefix: Path prefix for output files (without extension).
        num_designs: Number of designs to generate.
        contigs: Contig specification string (e.g., "A1-180/0 12-16").
        cyclic: Whether to generate cyclic peptides.
        cyc_chains: Chain(s) to make cyclic ('a' for self-cyclic, 'B' for binder).
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


def _get_chain_residue_range(pdb_path: str, chain_id: str) -> tuple[int, int]:
    """Extract the residue range for a given chain from a PDB file.

    Args:
        pdb_path: Path to the PDB file.
        chain_id: Chain ID to extract range for.

    Returns:
        Tuple of (start_residue, end_residue).

    Raises:
        ValueError: If the chain is not found or PDB cannot be parsed.
    """
    residue_numbers = []
    path = Path(pdb_path)

    if not path.exists():
        raise FileNotFoundError(f"PDB file not found: {pdb_path}")

    with open(path, "r") as f:
        for line in f:
            if line.startswith(("ATOM", "HETATM")):
                # PDB format: columns 22 = chain, 23-26 = residue number
                if len(line) >= 26:
                    chain = line[21]
                    if chain == chain_id:
                        try:
                            res_num = int(line[22:26].strip())
                            residue_numbers.append(res_num)
                        except ValueError:
                            continue

    if not residue_numbers:
        raise ValueError(f"Chain '{chain_id}' not found in PDB file: {pdb_path}")

    return (min(residue_numbers), max(residue_numbers))


def _build_command(config: RFDiffusionConfig) -> list[str]:
    """Build the RFdiffusion command from configuration.

    Args:
        config: RFDiffusionConfig instance with run parameters.

    Returns:
        List of command arguments for subprocess execution.
    """
    # Convert Python bool to lowercase string for Hydra/YAML
    cyclic_str = "true" if config.cyclic else "false"

    cmd = [
        MAMBA_PATH, "run", "-p", str(_ENV_PATH),
        "python", "scripts/run_inference.py",
        f"--config-name={config.config_name}",
        f"inference.output_prefix={config.output_prefix}",
        f"inference.num_designs={config.num_designs}",
        f"contigmap.contigs=[{config.contigs}]",
        f"inference.cyclic={cyclic_str}",
        f"inference.cyc_chains={config.cyc_chains!r}",
        f"diffuser.T={config.diffusion_steps}",
    ]

    if config.input_pdb:
        cmd.append(f"inference.input_pdb={config.input_pdb}")

    if config.hotspot_res:
        cmd.append(f"ppi.hotspot_res=[{config.hotspot_res}]")

    return cmd


def _run_rfdiffusion(config: RFDiffusionConfig, output_dir: str) -> GenerationResult:
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
    # Validate paths
    if not _RFDIFF_DIR.exists():
        raise FileNotFoundError(
            f"RFdiffusion directory not found: {_RFDIFF_DIR}\n"
            "Please ensure rfd_macro is properly linked in repo/"
        )

    if not _ENV_PATH.exists():
        raise FileNotFoundError(
            f"RFpeptides environment not found: {_ENV_PATH}\n"
            "Please create the conda environment first."
        )

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Build command
    cmd = _build_command(config)
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


def _parse_length(length: Union[int, tuple[int, int]]) -> tuple[int, int]:
    """Parse length parameter to (min, max) tuple."""
    if isinstance(length, int):
        return (length, length)
    return length


def generate_cyclic_backbone(
    peptide_length: Union[int, tuple[int, int]],
    num_designs: int,
    output_dir: str,
    diffusion_steps: int = 50,
    device: Optional[int] = None,
) -> GenerationResult:
    """Generate unconditional cyclic peptide backbones.

    This implements Use Case 6 (Structural Space Enumeration) from the RFpeptides
    paper. It generates diverse cyclic peptide backbones without any target
    protein, useful for exploring the structural landscape of macrocycles.

    Args:
        peptide_length: Length of the peptide in residues. Can be a single integer
            for fixed length, or a (min, max) tuple for variable length.
        num_designs: Number of designs to generate.
        output_dir: Directory to save output files.
        diffusion_steps: Number of diffusion timesteps (default: 50).
        device: CUDA device ID (e.g., 0, 1, 2). If None, uses default GPU.

    Returns:
        GenerationResult containing paths to generated PDB and TRB files.

    Example:
        >>> result = generate_cyclic_backbone(
        ...     peptide_length=10,
        ...     num_designs=100,
        ...     output_dir="./outputs/enumeration",
        ...     device=0,
        ... )
        >>> print(f"Generated {result.num_generated} backbones")
    """
    min_len, max_len = _parse_length(peptide_length)

    config = RFDiffusionConfig(
        output_prefix=str(Path(output_dir) / f"cyclic_{min_len}mer"),
        num_designs=num_designs,
        contigs=f"{min_len}-{max_len}",
        cyclic=True,
        cyc_chains="a",  # lowercase = self-cyclic
        diffusion_steps=diffusion_steps,
        device=device,
    )

    return _run_rfdiffusion(config, output_dir)


def design_binder(
    target_pdb: str,
    binder_length: Union[int, tuple[int, int]],
    num_designs: int,
    output_dir: str,
    target_chain: str = "A",
    target_residue_range: Optional[tuple[int, int]] = None,
    diffusion_steps: int = 50,
    device: Optional[int] = None,
    cyclic: bool = False,
) -> GenerationResult:
    """Design peptide binders against a target protein.

    This implements Use Cases 1a, 1c, and 4 from the RFpeptides paper. It designs
    peptide backbones that bind to a target protein structure without
    specific hotspot constraints.

    Args:
        target_pdb: Path to the target protein PDB file.
        binder_length: Length of the binder peptide in residues. Can be a single
            integer or a (min, max) tuple for variable length.
        num_designs: Number of designs to generate.
        output_dir: Directory to save output files.
        target_chain: Chain ID of the target protein (default: "A").
        target_residue_range: Optional (start, end) residue range to include from
            the target. If None, all residues from the target chain are included.
        diffusion_steps: Number of diffusion timesteps (default: 50).
        device: CUDA device ID (e.g., 0, 1, 2). If None, uses default GPU.
        cyclic: If True, generate cyclic peptide binders. Default is False (linear).

    Returns:
        GenerationResult containing paths to generated PDB and TRB files.

    Example:
        >>> result = design_binder(
        ...     target_pdb="./pdbs/target.pdb",
        ...     binder_length=(12, 16),
        ...     num_designs=50,
        ...     output_dir="./outputs/binders",
        ...     target_chain="A",
        ...     target_residue_range=(1, 180),
        ...     device=0,
        ...     cyclic=True,
        ... )
    """
    min_len, max_len = _parse_length(binder_length)
    target_path = Path(target_pdb)

    # Build contigs string - auto-detect range if not provided
    if target_residue_range:
        start, end = target_residue_range
    else:
        start, end = _get_chain_residue_range(target_pdb, target_chain)

    # Contigs format: [binder_length target_chain_range/0]
    # Binder comes first (becomes chain 'a'), target second
    contigs = f"{min_len}-{max_len} {target_chain}{start}-{end}/0"
    suffix = "_cyclic_binder" if cyclic else "_binder"
    output_prefix = target_path.stem + suffix

    config = RFDiffusionConfig(
        output_prefix=str(Path(output_dir) / output_prefix),
        num_designs=num_designs,
        input_pdb=str(target_pdb),
        contigs=contigs,
        cyclic=cyclic,
        cyc_chains="a" if cyclic else "",  # lowercase 'a' = self-cyclic binder (first chain)
        diffusion_steps=diffusion_steps,
        device=device,
    )

    return _run_rfdiffusion(config, output_dir)


# Alias for backward compatibility
def design_cyclic_binder(
    target_pdb: str,
    binder_length: Union[int, tuple[int, int]],
    num_designs: int,
    output_dir: str,
    target_chain: str = "A",
    target_residue_range: Optional[tuple[int, int]] = None,
    diffusion_steps: int = 50,
    device: Optional[int] = None,
) -> GenerationResult:
    """Design cyclic peptide binders against a target protein.

    This is an alias for design_binder(..., cyclic=True).
    See design_binder() for full documentation.
    """
    return design_binder(
        target_pdb=target_pdb,
        binder_length=binder_length,
        num_designs=num_designs,
        output_dir=output_dir,
        target_chain=target_chain,
        target_residue_range=target_residue_range,
        diffusion_steps=diffusion_steps,
        device=device,
        cyclic=True,
    )


def design_binder_with_hotspots(
    target_pdb: str,
    hotspot_residues: list[int],
    binder_length: Union[int, tuple[int, int]],
    num_designs: int,
    output_dir: str,
    target_chain: str = "A",
    target_residue_range: Optional[tuple[int, int]] = None,
    diffusion_steps: int = 50,
    device: Optional[int] = None,
    cyclic: bool = False,
) -> GenerationResult:
    """Design peptide binders with epitope-specific targeting.

    This implements Use Cases 1b, 2, 3a, and 3b from the RFpeptides paper. It
    designs peptide backbones that specifically target designated hotspot
    residues on the target protein, enabling epitope-focused binder design.

    The hotspot guidance steers the diffusion process to generate binders that
    interact with the specified residues, which is useful for:
    - Targeting specific epitopes for immunological applications
    - Designing competitive inhibitors of protein-protein interactions
    - Focusing binding on functionally important residues

    Args:
        target_pdb: Path to the target protein PDB file.
        hotspot_residues: List of residue numbers to target on the target protein.
            These residues will be used to guide the binder design process.
        binder_length: Length of the binder peptide in residues. Can be a single
            integer or a (min, max) tuple for variable length.
        num_designs: Number of designs to generate.
        output_dir: Directory to save output files.
        target_chain: Chain ID of the target protein (default: "A").
        target_residue_range: Optional (start, end) residue range to include from
            the target. If None, all residues from the target chain are included.
        diffusion_steps: Number of diffusion timesteps (default: 50).
        device: CUDA device ID (e.g., 0, 1, 2). If None, uses default GPU.
        cyclic: If True, generate cyclic peptide binders. Default is False (linear).

    Returns:
        GenerationResult containing paths to generated PDB and TRB files.

    Example:
        >>> result = design_binder_with_hotspots(
        ...     target_pdb="./pdbs/target.pdb",
        ...     hotspot_residues=[46, 48, 49, 50, 60, 63],
        ...     binder_length=(13, 18),
        ...     num_designs=50,
        ...     output_dir="./outputs/epitope_binders",
        ...     target_chain="A",
        ...     target_residue_range=(1, 117),
        ...     device=0,
        ...     cyclic=True,
        ... )
    """
    min_len, max_len = _parse_length(binder_length)
    target_path = Path(target_pdb)

    # Build contigs string - auto-detect range if not provided
    if target_residue_range:
        start, end = target_residue_range
    else:
        start, end = _get_chain_residue_range(target_pdb, target_chain)

    # Contigs format: [binder_length target_chain_range/0]
    # Binder comes first (becomes chain 'a'), target second
    contigs = f"{min_len}-{max_len} {target_chain}{start}-{end}/0"

    # Format hotspot residues: [A46,A48,A49,...]
    hotspot_str = ",".join(f"{target_chain}{res}" for res in hotspot_residues)

    suffix = "_cyclic_epitope" if cyclic else "_epitope"
    output_prefix = target_path.stem + suffix

    config = RFDiffusionConfig(
        output_prefix=str(Path(output_dir) / output_prefix),
        num_designs=num_designs,
        input_pdb=str(target_pdb),
        contigs=contigs,
        cyclic=cyclic,
        cyc_chains="a" if cyclic else "",  # lowercase 'a' = self-cyclic binder (first chain)
        diffusion_steps=diffusion_steps,
        hotspot_res=hotspot_str,
        device=device,
    )

    return _run_rfdiffusion(config, output_dir)


# Alias for backward compatibility
def design_cyclic_binder_with_hotspots(
    target_pdb: str,
    hotspot_residues: list[int],
    binder_length: Union[int, tuple[int, int]],
    num_designs: int,
    output_dir: str,
    target_chain: str = "A",
    target_residue_range: Optional[tuple[int, int]] = None,
    diffusion_steps: int = 50,
    device: Optional[int] = None,
) -> GenerationResult:
    """Design cyclic peptide binders with epitope-specific targeting.

    This is an alias for design_binder_with_hotspots(..., cyclic=True).
    See design_binder_with_hotspots() for full documentation.
    """
    return design_binder_with_hotspots(
        target_pdb=target_pdb,
        hotspot_residues=hotspot_residues,
        binder_length=binder_length,
        num_designs=num_designs,
        output_dir=output_dir,
        target_chain=target_chain,
        target_residue_range=target_residue_range,
        diffusion_steps=diffusion_steps,
        device=device,
        cyclic=True,
    )
