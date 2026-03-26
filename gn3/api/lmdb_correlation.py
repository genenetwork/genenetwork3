"""API endpoints for LMDB-based correlation."""
import os
import time
from flask import Blueprint, jsonify, request, current_app

from gn3.computations.lmdb_correlation import (
    CorrelationInput,
    run_lmdb_correlation,
    LMDBCorrelationError
)


lmdb_corr = Blueprint("lmdb_corr", __name__)


@lmdb_corr.route("/lmdb_status/<string:dataset_name>", methods=["GET"])
def check_lmdb_status(dataset_name: str):
    """Check if LMDB dataset exists and is available.
    
    This endpoint allows GN2 (or other clients) to check if a dataset
    is available in LMDB format before attempting correlation.
    
    Args:
        dataset_name: Name of dataset (e.g., "HC_M2_0606_P")
    
    Returns:
        {
            "available": true,
            "dataset_name": "HC_M2_0606_P",
            "lmdb_path": "/path/to/lmdb"
        }
    """
    lmdb_base = current_app.config.get("LMDB_DATA_PATH")
    if not lmdb_base:
        return jsonify(
            available=False,
            dataset_name=dataset_name,
            error="LMDB_DATA_PATH not configured"
        ), 503
    
    lmdb_path = os.path.join(lmdb_base, dataset_name)
    
    # Check if LMDB files exist
    has_data = os.path.exists(os.path.join(lmdb_path, "data.mdb"))
    has_lock = os.path.exists(os.path.join(lmdb_path, "lock.mdb"))
    
    if has_data and has_lock:
        return jsonify(
            available=True,
            dataset_name=dataset_name,
            lmdb_path=lmdb_path
        )
    else:
        return jsonify(
            available=False,
            dataset_name=dataset_name,
            lmdb_path=lmdb_path if os.path.isdir(lmdb_path) else None
        )


@lmdb_corr.route("/lmdb_corr", methods=["POST"])
def compute_lmdb_corr():
    """Compute correlation using LMDB dataset.
    
    This endpoint uses pre-computed LMDB files for fast correlation
    without CSV generation or database queries.
    
    Request JSON:
        {
            "dataset_name": "HC_M2_0606_P",
            "trait_vals": [25.08, 72.02, 47.56, ...],
            "strains": ["BXD11", "BXD12", "BXD45", ...],
            "method": "pearson",
            "parallel": true,
            "top_n": 500
        }
    
    Returns:
        {
            "status": "success",
            "results": {...},
            "elapsed_time": "1.23s"
        }
    """
    start = time.time()
    
    data = request.get_json()
    if not data:
        return jsonify(error="No request data"), 400
    
    # Validate required fields
    required = ["dataset_name", "trait_vals", "strains"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify(error=f"Missing fields: {missing}"), 400
    
    # Build input object
    try:
        input_data = CorrelationInput(
            dataset_name=data["dataset_name"],
            trait_vals=data["trait_vals"],
            strains=data["strains"],
            method=data.get("method", "pearson"),
            parallel=data.get("parallel", True),
            top_n=data.get("top_n", 500)
        )
    except (TypeError, ValueError) as e:
        return jsonify(error=f"Invalid input: {e}"), 400
    
    # Run correlation
    try:
        results = run_lmdb_correlation(input_data)
        
        return jsonify(
            status="success",
            results=results,
            elapsed_time=f"{time.time() - start:.2f}s",
            dataset_name=input_data.dataset_name,
            config={
                "method": input_data.method,
                "parallel": input_data.parallel,
                "num_strains": len(input_data.strains),
                "num_results": len(results)
            }
        )
    
    except LMDBCorrelationError as e:
        current_app.logger.error("LMDB correlation failed: %s", e)
        return jsonify(error=str(e)), 400
