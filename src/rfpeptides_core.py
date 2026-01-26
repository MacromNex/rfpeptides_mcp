"""Core RFpeptides backbone generation functions.

This module provides three core functions for cyclic peptide backbone generation
using RFdiffusion:

1. generate_cyclic_backbone: Unconditional cyclic peptide backbone generation
2. design_cyclic_binder: Design cyclic peptide binders against a target protein
3. design_cyclic_binder_with_hotspots: Design with epitope-specific targeting
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Union, Optional

from .runner import run_rfdiffusion, RFDiffusionConfig


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

    Returns:
        GenerationResult containing paths to generated PDB and TRB files.

    Example:
        >>> result = generate_cyclic_backbone(
        ...     peptide_length=10,
        ...     num_designs=100,
        ...     output_dir="./outputs/enumeration"
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
    )

    return run_rfdiffusion(config, output_dir)


def design_cyclic_binder(
    target_pdb: str,
    binder_length: Union[int, tuple[int, int]],
    num_designs: int,
    output_dir: str,
    target_chain: str = "A",
    target_residue_range: Optional[tuple[int, int]] = None,
    diffusion_steps: int = 50,
) -> GenerationResult:
    """Design cyclic peptide binders against a target protein.

    This implements Use Cases 1a, 1c, and 4 from the RFpeptides paper. It designs
    cyclic peptide backbones that bind to a target protein structure without
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

    Returns:
        GenerationResult containing paths to generated PDB and TRB files.

    Example:
        >>> result = design_cyclic_binder(
        ...     target_pdb="./pdbs/target.pdb",
        ...     binder_length=(12, 16),
        ...     num_designs=50,
        ...     output_dir="./outputs/binders",
        ...     target_chain="A",
        ...     target_residue_range=(1, 180),
        ... )
    """
    min_len, max_len = _parse_length(binder_length)
    target_path = Path(target_pdb)

    # Build contigs string - auto-detect range if not provided
    if target_residue_range:
        start, end = target_residue_range
    else:
        start, end = _get_chain_residue_range(target_pdb, target_chain)

    contigs = f"{target_chain}{start}-{end}/0 {min_len}-{max_len}"
    output_prefix = target_path.stem + "_binder"

    config = RFDiffusionConfig(
        output_prefix=str(Path(output_dir) / output_prefix),
        num_designs=num_designs,
        input_pdb=str(target_pdb),
        contigs=contigs,
        cyclic=True,
        cyc_chains="B",  # uppercase = binder chain
        diffusion_steps=diffusion_steps,
    )

    return run_rfdiffusion(config, output_dir)


def design_cyclic_binder_with_hotspots(
    target_pdb: str,
    hotspot_residues: list[int],
    binder_length: Union[int, tuple[int, int]],
    num_designs: int,
    output_dir: str,
    target_chain: str = "A",
    target_residue_range: Optional[tuple[int, int]] = None,
    diffusion_steps: int = 50,
) -> GenerationResult:
    """Design cyclic peptide binders with epitope-specific targeting.

    This implements Use Cases 1b, 2, 3a, and 3b from the RFpeptides paper. It
    designs cyclic peptide backbones that specifically target designated hotspot
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

    Returns:
        GenerationResult containing paths to generated PDB and TRB files.

    Example:
        >>> result = design_cyclic_binder_with_hotspots(
        ...     target_pdb="./pdbs/target.pdb",
        ...     hotspot_residues=[46, 48, 49, 50, 60, 63],
        ...     binder_length=(13, 18),
        ...     num_designs=50,
        ...     output_dir="./outputs/epitope_binders",
        ...     target_chain="A",
        ...     target_residue_range=(1, 117),
        ... )
    """
    min_len, max_len = _parse_length(binder_length)
    target_path = Path(target_pdb)

    # Build contigs string - auto-detect range if not provided
    if target_residue_range:
        start, end = target_residue_range
    else:
        start, end = _get_chain_residue_range(target_pdb, target_chain)

    contigs = f"{target_chain}{start}-{end}/0 {min_len}-{max_len}"

    # Format hotspot residues: [A46,A48,A49,...]
    hotspot_str = ",".join(f"{target_chain}{res}" for res in hotspot_residues)

    output_prefix = target_path.stem + "_epitope"

    config = RFDiffusionConfig(
        output_prefix=str(Path(output_dir) / output_prefix),
        num_designs=num_designs,
        input_pdb=str(target_pdb),
        contigs=contigs,
        cyclic=True,
        cyc_chains="B",
        diffusion_steps=diffusion_steps,
        hotspot_res=hotspot_str,
    )

    return run_rfdiffusion(config, output_dir)
