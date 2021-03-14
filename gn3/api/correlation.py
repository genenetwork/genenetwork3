"""Endpoints for running correlations"""
from flask import jsonify
from flask import Blueprint
from flask import request

from gn3.computations.correlations import compute_all_sample_correlation


correlation = Blueprint("correlation", __name__)


@correlation.route("/sample_r", methods=["POST"])
def compute_sample_r():
    """correlation endpoint for computing sample r correlations\
    api expects the trait data  and aslo the target_dataset  data"""
    correlation_input = request.json
    corr_method = correlation_input.get("corr_method")
    this_trait = correlation_input.get("this_trait")
    target_dataset = correlation_input.get("target_dataset")

    correlation_results = compute_all_sample_correlation(corr_method=corr_method,
                                                         this_trait=this_trait,
                                                         target_dataset=target_dataset)

    return jsonify({
        "corr_results": correlation_results
    })
