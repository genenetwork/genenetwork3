"""Endpoints for computing correlation"""
import json
from flask import Blueprint
from flask import jsonify
from flask import request

from gn3.correlation.correlation_computations import get_loading_page_data
from gn3.correlation.correlation_computations import get_loading_page_data
from gn3.correlation.correlation_computations import get_loading_page_data
from gn3.correlation.show_corr_results import CorrelationResults

correlation = Blueprint("correlation", __name__)


@correlation.route("/corr_compute", methods=["POST"])
def corr_compute_page():
    """api for doing the actual correlation"""

    initial_start_vars = request.json
    start_vars_container = get_loading_page_data(
        initial_start_vars=initial_start_vars)


    start_vars = start_vars_container["start_vars"]

    corr_object = CorrelationResults(
        start_vars=start_vars)

    # return cor

    corr_results = corr_object.do_correlation(start_vars=start_vars)
    # possibility of file being so large cause of the not sure whether to return a file

    try:
        corr_results =json.loads(json.dumps(corr_results, default=lambda o: o.__dict__))

        return corr_results
    except Exception as e:
        return jsonify({"error": str(e)})


@correlation.route("/")
def index() -> str:
    """Test endpoint"""
    return jsonify(result="hello world")
