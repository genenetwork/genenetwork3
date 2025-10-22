"""Endpoints for running correlations"""
import sys
import logging
from functools import reduce

import redis
from flask import jsonify
from flask import Blueprint
from flask import request
from flask import current_app

from gn3.db_utils import database_connection
from gn3.commands import run_sample_corr_cmd
from gn3.responses.pcorrs_responses import build_response
from gn3.computations.correlations import map_shared_keys_to_values
from gn3.computations.correlations import compute_tissue_correlation
from gn3.computations.correlations import compute_all_lit_correlation
from gn3.commands import (
    run_async_cmd, compute_job_queue, compose_pcorrs_command)

correlation = Blueprint("correlation", __name__)


@correlation.route("/sample_x/<string:corr_method>", methods=["POST"])
def compute_sample_integration(corr_method="pearson"):
    """temporary api to  help integrate genenetwork2  to genenetwork3 """

    correlation_input = request.get_json()

    target_samplelist = correlation_input.get("target_samplelist")
    target_data_values = correlation_input.get("target_dataset")
    this_trait_data = correlation_input.get("trait_data")

    results = map_shared_keys_to_values(target_samplelist, target_data_values)
    correlation_results = run_sample_corr_cmd(
        corr_method, this_trait_data, results)

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

    correlation_results = run_sample_corr_cmd(
        corr_method, this_trait_data, target_dataset_data)

    return jsonify({
        "corr_results": correlation_results
    })


@correlation.route("/lit_corr/<string:species>/<int:gene_id>", methods=["POST"])
def compute_lit_corr(species=None, gene_id=None):
    """Api endpoint for doing lit correlation.results for lit correlation\
    are fetched from the database this is the only case where the db\
    might be needed for actual computing of the correlation results
    """

    with database_connection(current_app.config["SQL_URI"], logger=current_app.logger) as conn:
        target_traits_gene_ids = request.get_json()
        target_trait_gene_list = list(target_traits_gene_ids.items())

        lit_corr_results = compute_all_lit_correlation(
            conn=conn, trait_lists=target_trait_gene_list,
            species=species, gene_id=gene_id)

        return jsonify(lit_corr_results)


@correlation.route("/tissue_corr/<string:corr_method>", methods=["POST"])
def compute_tissue_corr(corr_method="pearson"):
    """Api endpoint fr doing tissue correlation"""
    tissue_input_data = request.get_json()
    primary_tissue_dict = tissue_input_data["primary_tissue"]
    target_tissues_dict = tissue_input_data["target_tissues_dict"]

    results = compute_tissue_correlation(primary_tissue_dict=primary_tissue_dict,
                                         target_tissues_data=target_tissues_dict,
                                         corr_method=corr_method)

    return jsonify(results)


@correlation.route("/partial", methods=["POST"])
def partial_correlation():
    """API endpoint for partial correlations."""
    def trait_fullname(trait):
        return f"{trait['dataset']}::{trait['trait_name']}"

    def __field_errors__(args):
        def __check__(acc, field):
            if args.get(field) is None:
                return acc + (f"Field '{field}' missing",)
            return acc
        return __check__

    def __errors__(request_data, fields):
        errors = tuple()
        if request_data is None:
            return ("No request data",)

        return reduce(__field_errors__(request_data), fields, errors)

    args = request.get_json()
    with_target_db = args.get("with_target_db", True)
    request_errors = __errors__(
        args, ("primary_trait", "control_traits",
               ("target_db" if with_target_db else "target_traits"),
               "method"))
    if request_errors:
        return build_response({
            "status": "error",
            "messages": request_errors,
            "error_type": "Client Error"})

    with redis.Redis() as conn:
        if with_target_db:
            command = compose_pcorrs_command(
                trait_fullname(args["primary_trait"]),
                tuple(
                    trait_fullname(trait) for trait in args["control_traits"]),
                args["method"], target_database=args["target_db"],
                criteria=int(args.get("criteria", 500)))
        else:
            command = compose_pcorrs_command(
                trait_fullname(args["primary_trait"]),
                tuple(
                    trait_fullname(trait) for trait in args["control_traits"]),
                args["method"], target_traits=tuple(
                    trait_fullname(trait) for trait in args["target_traits"]))

        queueing_results = run_async_cmd(
            conn=conn,
            cmd=command,
            job_queue=compute_job_queue(current_app),
            options={
                "env": {
                    "PYTHONPATH": ":".join(sys.path),
                    "SQL_URI": current_app.config["SQL_URI"]
                },
            },
            log_level=logging.getLevelName(
                current_app.logger.getEffectiveLevel()).lower())
        return build_response({
            "status": "success",
            "results": queueing_results,
            "queued": True
        })
