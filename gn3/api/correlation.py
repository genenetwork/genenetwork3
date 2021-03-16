"""Endpoints for running correlations"""
from unittest import mock

from flask import jsonify
from flask import Blueprint
from flask import request

from gn3.computations.correlations import compute_all_sample_correlation
from gn3.computations.correlations import compute_all_lit_correlation


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


@correlation.route("/lit_corr/<string:species>/<int:gene_id>", methods=["POST"])
def compute_lit_corr(species=None, gene_id=None):
    """api endpoint for doing lit correlation.results for lit correlation\
    are fetched from the database this is the only case where the db\
    might be needed for actual computing of the correlation results"""

    database_instance = mock.Mock()
    target_traits_gene_ids = request.get_json()

    lit_corr_results = compute_all_lit_correlation(
        database_instance=database_instance, trait_lists=target_traits_gene_ids,
        species=species, gene_id=gene_id)

    return jsonify(lit_corr_results)
