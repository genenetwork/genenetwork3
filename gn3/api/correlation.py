"""Endpoints for running correlations"""
from flask import jsonify
from flask import Blueprint
from flask import request

from gn3.computations.correlations import compute_sample_r_correlation


correlation = Blueprint("correlation", __name__)


@correlation.route("/")
def hello():
    """hello world api endpoint"""
    return jsonify({"response": "hello there"})


@correlation.route("/sample_r", methods=["Post"])
def compute_sample_r():
    """correlation endpoint for computing sample r correlations"""
    correlation_input = request.json
    corr_method = correlation_input["corr_method"]
    trait_vals = correlation_input["trait_vals"]
    target_samples_vals = correlation_input["target_samples_vals"]
    # corr_method: str, trait_vals, target_samples_vals

    correlation_results = compute_sample_r_correlation(corr_method=corr_method,
                                                       trait_vals=trait_vals,
                                                       target_samples_vals=target_samples_vals)

    return jsonify({
        "results": correlation_results
    })
