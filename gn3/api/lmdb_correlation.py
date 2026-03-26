"""API endpoints for LMDB-based correlation."""
import time
from flask import Blueprint, jsonify, request, current_app

from gn3.computations.lmdb_correlation import (
    CorrelationInput,
    run_lmdb_correlation,
    LMDBCorrelationError
)


lmdb_corr = Blueprint("lmdb_corr", __name__)


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
