"""Endpoints for computing correlation"""
from flask import Blueprint
from flask import jsonify

from gn3.correlation.correlation_computations import get_loading_page_data
from gn3.correlation.show_corr_results import CorrelationResults

correlation = Blueprint("correlation", __name__)


@correlation.route("/corr_compute")
def corr_compute_page():
    """api for doing the actual correlation"""

    start_vars_container = get_loading_page_data(initial_start_vars=None,
                                                 create_dataset=None, get_genofile_samplelist=None)

    corr_object = CorrelationResults(
        start_vars=start_vars_container)

    corr_results = corr_object.__dict__
    # print(corr_results)
    # possibility of file being so large cause of the not sure whether to return a file
    # initial setup for return type

    return jsonify({"corr_results": {
        "dataset": corr_results
    }})


@correlation.route("/")
def index() -> str:
    """Test endpoint"""
    return jsonify(result="hello world")
