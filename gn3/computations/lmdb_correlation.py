"""LMDB-based correlation computation.

This module provides optimized correlation computation using pre-computed
LMDB files, bypassing CSV generation and database queries.
"""
import os
import json
import subprocess
from dataclasses import dataclass
from typing import Optional

from flask import current_app
from gn3.computations.qtlreaper import create_output_directory
from gn3.chancy import random_string


class LMDBCorrelationError(Exception):
    """Exception raised for LMDB correlation errors."""
    pass


@dataclass(frozen=True)
class CorrelationInput:
    """Input data for correlation computation."""
    dataset_name: str
    trait_vals: list[float]
    strains: list[str]
    method: str = "pearson"
    parallel: bool = True
    top_n: int = 500


def get_lmdb_path(dataset_name: str) -> str:
    """Construct full LMDB path from dataset name.

    Args:
        dataset_name: Name of dataset (e.g., "HC_M2_0606_P")

    Returns:
        Full path to LMDB directory

    Raises:
        LMDBCorrelationError: If LMDB_DATA_PATH not configured
    """
    base_path = current_app.config.get("LMDB_DATA_PATH")
    if not base_path:
        raise LMDBCorrelationError("LMDB_DATA_PATH not configured")
    return os.path.join(base_path, dataset_name)


def validate_dataset(lmdb_path: str) -> None:
    """Validate that LMDB dataset exists and is valid.

    Args:
        lmdb_path: Full path to LMDB directory

    Raises:
        LMDBCorrelationError: If dataset doesn't exist or is invalid
    """
    if not os.path.isdir(lmdb_path):
        raise LMDBCorrelationError(f"Dataset not found: {lmdb_path}")

    required_files = ["data.mdb", "lock.mdb"]
    missing = [f for f in required_files if not os.path.exists(
        os.path.join(lmdb_path, f))]
    if missing:
        raise LMDBCorrelationError(
            f"Invalid LMDB dataset, missing: {', '.join(missing)}")


def validate_input(data: CorrelationInput) -> None:
    """Validate correlation input data.

    Args:
        data: CorrelationInput to validate

    Raises:
        LMDBCorrelationError: If validation fails
    """
    if len(data.trait_vals) != len(data.strains):
        raise LMDBCorrelationError(
            f"Array length mismatch: {len(data.strains)} strains but "
            f"{len(data.trait_vals)} values"
        )

    if not all(isinstance(s, str) for s in data.strains):
        raise LMDBCorrelationError("All strains must be strings")

    if data.method not in ("pearson", "spearman"):
        raise LMDBCorrelationError(f"Invalid method: {data.method}")


def create_json_config(
    tmp_dir: str,
    lmdb_path: str,
    data: CorrelationInput
) -> tuple[str, str]:
    """Create JSON configuration for Rust correlation.

    Args:
        tmp_dir: Temporary directory for files
        lmdb_path: Path to LMDB dataset
        data: Correlation input data

    Returns:
        Tuple of (output_file_path, json_config_path)
    """
    json_file = os.path.join(tmp_dir, f"{random_string(10)}.json")
    output_file = os.path.join(tmp_dir, f"{random_string(10)}.txt")

    config = {
        "file_path": lmdb_path,
        "x_vals": data.trait_vals,
        "strains": data.strains,
        "sample_values": "input_trait",
        "method": data.method,
        "file_delimiter": ",",
        "output_file": output_file,
        "parallel": data.parallel
    }

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(config, f)

    return output_file, json_file


def parse_results(output_file: str, top_n: int) -> dict:
    """Parse correlation results from output file.

    Args:
        output_file: Path to output file
        top_n: Maximum number of results to return

    Returns:
        Dictionary of correlation results
    """
    results = {}
    with open(output_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx >= top_n:
                break
            trait, coeff, pval, overlap = line.rstrip().split(",")
            results[trait] = {
                "corr_coefficient": coeff,
                "p_value": pval,
                "num_overlap": overlap
            }
    return results


def run_lmdb_correlation(data: CorrelationInput, tmpdir: str = "/tmp") -> dict:
    """Run correlation using LMDB dataset.

    Args:
        data: CorrelationInput with all parameters
        tmpdir: Temporary directory for output files

    Returns:
        Dictionary of correlation results

    Raises:
        LMDBCorrelationError: If computation fails
    """
    # Get and validate paths
    lmdb_path = get_lmdb_path(data.dataset_name)
    validate_dataset(lmdb_path)

    # Validate input
    validate_input(data)

    # Get correlation command
    cmd = current_app.config.get("CORRELATION_COMMAND")
    if not cmd:
        raise LMDBCorrelationError("CORRELATION_COMMAND not configured")

    # Create temp directory and config
    tmp_dir = f"{tmpdir}/correlation"
    create_output_directory(tmp_dir)

    output_file, json_file = create_json_config(tmp_dir, lmdb_path, data)

    # Run correlation - same pattern as rust_correlation.py
    command_list = [cmd, json_file, tmpdir]
    try:
        subprocess.run(command_list, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise LMDBCorrelationError(
            f"Correlation failed: {e.stderr.decode()}") from e

    # Parse and return results
    return parse_results(output_file, data.top_n)
