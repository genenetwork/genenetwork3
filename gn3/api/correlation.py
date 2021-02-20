"""Endpoints for computing correlation"""
from flask import Blueprint
from flask import jsonify

correlation = Blueprint("correlation", __name__)


@correlation.route("/corr_compute", methods=["POST"])
def corr_compute_page():

    start_vars_container = get_loading_page_data(initial_start_vars=None,create_dataset=None,get_loading_page_data=None)

    corr_object = show_corr_results.CorrelationResults(
        start_vars=start_vars_container)

    corr_results = corr_object.__dict__
    # possibility of file being so large cause of the not sure whether to return a file
    # initial setup for return type

    return jsonify({"corr_results":{
        "dataset":"dataset"
        }})


@correlation.route("/")
def index() -> str:
    """Test endpoint"""
    return jsonify(result="hello world")
