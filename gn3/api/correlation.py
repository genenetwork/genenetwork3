"""Endpoints for computing correlation"""
import json
from flask import Blueprint
from flask import jsonify
from flask import request

from gn3.correlation.correlation_computations import get_loading_page_data
from gn3.correlation.correlation_computations import compute_correlation
from gn3.correlation.show_corr_results import CorrelationResults

correlation = Blueprint("correlation", __name__)


@correlation.route("/corr_compute", methods=["POST"])
def corr_compute_page():
    """api for doing  correlation"""

    initial_start_vars = request.json

    corr_results = compute_correlation(init_start_vars=initial_start_vars)
    try:
        corr_results = json.loads(json.dumps(
            corr_results, default=lambda o: o.__dict__))

        return corr_results
    except Exception as e:
        return jsonify({"error": str(e)})
