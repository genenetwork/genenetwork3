"""
Api endpoints for lmdb traits
"""


import os
import json
import re
from typing import Optional

import lmdb
import numpy as np
from flask import Blueprint, current_app, jsonify


lmdb_traits = Blueprint("lmdb_traits", __name__)


@lmdb_traits.route("/traits/<path:trait_spec>.json", methods=["GET"])
def get_phenotype(trait_spec: str):  # pylint: disable=too-many-locals
    """Fetch phenotype data.

    Path parameters:
        trait_spec: Format is <dataset>_<trait_id>
                    Example: BXDPublish_12315
    Returns:
        JSON object with strain names as keys, each containing value and se:
        {
            "BXD1": {"value": 5.67, "se": 0.12},
            "BXD2": {"value": 4.32, "se": 0.15},
            ...
        }

    Example:
        GET /dataset/phenotype/BXDPublish_12315
    """
    # Parse the trait specification
    match = re.match(r"^(.+?)_(\d+)$", trait_spec)
    if not match:
        return jsonify({
            "error": "Invalid trait specification",
            "message": "Format should be <dataset>_<trait_id>, e.g., BXDPublish_12315",
        }), 400

    dataset, trait_id = match.groups()
    trait_id = str(int(trait_id))  # Normalize: "00123" -> "123"
    lmdb_path = os.path.join(
        current_app.config["LMDB_DATA_PATH"], dataset)
    with open_lmdb(lmdb_path) as env:
        with env.begin() as txn:
            metadata = read_metadata(txn)
            # Fetch values
            values = fetch_trait_row(
                txn, trait_id, metadata, b"pheno_matrix")

            # Try to fetch SE values
            se_values = None
            try:
                se_values = fetch_trait_row(
                    txn, trait_id, metadata, b"pheno_se_matrix")
            except KeyError:
                pass

            # Build response with both value and SE
            strains = metadata["strains"]
            data = {}

            for idx, strain in enumerate(strains):
                entry = {}

                value = values[idx]
                if not np.isnan(value):
                    entry["value"] = float(value)
                    # you cannot have SE without a value enforcing this here
                    if se_values is not None:
                        se_val = se_values[idx]
                        if not np.isnan(se_val):
                            entry["SE"] = float(se_val)

                if entry:
                    data[strain] = entry
            return jsonify(data)


def open_lmdb(db_path: str) -> lmdb.Environment:
    """Open an LMDB environment for reading."""
    return lmdb.open(db_path, readonly=True, lock=False)


def read_metadata(txn: lmdb.Transaction) -> dict:
    """Read and decode the metadata JSON from an open transaction."""
    raw = txn.get(b"pheno_metadata")
    if raw is None:
        raise KeyError("Metadata not found in LMDB")
    return json.loads(raw.decode("utf-8"))


def fetch_trait_row(
    txn: lmdb.Transaction,
    trait_name: str,
    metadata: dict,
    matrix_key: bytes = b"pheno_matrix",
) -> np.ndarray:
    """Fetch a single trait row from the matrix by slicing the raw bytes.

    Args:
        txn: Open LMDB transaction
        trait_name: Name/ID of the trait to fetch
        metadata: Decoded metadata dict
        matrix_key: Key for the matrix in LMDB (pheno_matrix or pheno_se_matrix)

    Returns:
        1D numpy array of values for this trait across all strains
    """
    traits = metadata["traits"]

    if trait_name not in traits:
        raise KeyError(f"Trait '{trait_name}' not found")

    row_idx = traits.index(trait_name)
    dtype = np.dtype(metadata["dtype"])
    bytes_per_row = metadata["columns"] * dtype.itemsize
    start = row_idx * bytes_per_row

    raw = txn.get(matrix_key)
    if raw is None:
        raise KeyError(f"Matrix '{matrix_key.decode()}' not found in LMDB")

    return np.frombuffer(raw, dtype=dtype, count=metadata["columns"], offset=start)


def build_trait_response(
    strains: list[str],
    values: np.ndarray,
    se_values: Optional[np.ndarray] = None,
) -> dict:
    """Build the JSON response for a trait query.

    Returns a dict with strain names as keys and value/SE pairs as values.
    NaN values are converted to null in JSON.
    """
    result = {}

    for idx, strain in enumerate(strains):
        value = values[idx]

        # Convert numpy types to Python native types
        # Convert NaN to None (which becomes null in JSON)
        if np.isnan(value):
            py_value = None
        else:
            py_value = float(value)

        if se_values is not None:
            se_val = se_values[idx]
            py_se = None if np.isnan(se_val) else float(se_val)
            result[strain] = {"value": py_value, "se": py_se}
        else:
            result[strain] = {"value": py_value, "se": None}

    return result
