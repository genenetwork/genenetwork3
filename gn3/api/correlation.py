"""Endpoints for running correlations"""
from flask import jsonify
from flask import Blueprint
from flask import request

from gn3.computations.correlations import compute_all_sample_correlation
from gn3.computations.correlations import compute_all_lit_correlation
from gn3.computations.correlations import compute_all_tissue_correlation
from gn3.computations.correlations import map_shared_keys_to_values
from gn3.db_utils import database_connector

correlation = Blueprint("correlation", __name__)


@correlation.route("/sample_x/<string:corr_method>", methods=["POST"])
def compute_sample_integration(corr_method="pearson"):
    """temporary api to  help integrate genenetwork2  to genenetwork3 """

    correlation_input = request.get_json()

    target_samplelist = correlation_input.get("target_samplelist")
    target_data_values = correlation_input.get("target_dataset")
    this_trait_data = correlation_input.get("trait_data")

    results = map_shared_keys_to_values(target_samplelist, target_data_values)
    correlation_results = compute_all_sample_correlation(corr_method=corr_method,
                                                         this_trait=this_trait_data,
                                                         target_dataset=results)

    return jsonify(correlation_results)


@correlation.route("/sample_r/<string:corr_method>", methods=["POST"])
def compute_sample_r(corr_method="pearson"):
    """Correlation endpoint for computing sample r correlations\
    api expects the trait data with has the trait and also the\
    target_dataset  data
    """
    correlation_input = request.get_json()

    # xtodo move code below to compute_all_sampl correlation
    this_trait_data = correlation_input.get("this_trait")
    target_dataset_data = correlation_input.get("target_dataset")

    correlation_results = compute_all_sample_correlation(corr_method=corr_method,
                                                         this_trait=this_trait_data,
                                                         target_dataset=target_dataset_data)

    return jsonify({
        "corr_results": correlation_results
    })


@correlation.route("/lit_corr/<string:species>/<int:gene_id>", methods=["POST"])
def compute_lit_corr(species=None, gene_id=None):
    """Api endpoint for doing lit correlation.results for lit correlation\
    are fetched from the database this is the only case where the db\
    might be needed for actual computing of the correlation results
    """

    conn, _cursor_object = database_connector()
    target_traits_gene_ids = request.get_json()
    target_trait_gene_list = list(target_traits_gene_ids.items())

    lit_corr_results = compute_all_lit_correlation(
        conn=conn, trait_lists=target_trait_gene_list,
        species=species, gene_id=gene_id)

    conn.close()

    return jsonify(lit_corr_results)


@correlation.route("/tissue_corr/<string:corr_method>", methods=["POST"])
def compute_tissue_corr(corr_method="pearson"):
    """Api endpoint fr doing tissue correlation"""
    tissue_input_data = request.get_json()
    primary_tissue_dict = tissue_input_data["primary_tissue"]
    target_tissues_dict = tissue_input_data["target_tissues_dict"]

    results = compute_all_tissue_correlation(primary_tissue_dict=primary_tissue_dict,
                                             target_tissues_data=target_tissues_dict,
                                             corr_method=corr_method)

    return jsonify(results)
