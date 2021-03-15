"""Endpoints for running correlations"""
from flask import jsonify
from flask import Blueprint
from flask import request

from gn3.computations.correlations import compute_all_sample_correlation


correlation = Blueprint("correlation", __name__)


@correlation.route("/sample_r/<string:corr_method>", methods=["POST"])
def compute_sample_r(corr_method):
    """correlation endpoint for computing sample r correlations\
    api expects the trait data with has the trait and also the\
    target_dataset  data"""
    correlation_input = request.get_json()
    this_trait_data = correlation_input.get("this_trait")
    target_datasets = correlation_input.get("target_dataset")

    correlation_results = compute_all_sample_correlation(corr_method=corr_method,
                                                         this_trait=this_trait_data,
                                                         target_dataset=target_datasets)

    return jsonify({
        "corr_results": correlation_results
    })
