"""this module contains the all endpoints for traits"""
from unittest import mock

from flask import Blueprint
from flask import jsonify
from flask import request

from gn3.computations.traits import fetch_trait
from gn3.computations.traits import get_trait_info_data
trait = Blueprint("trait", __name__)


@trait.route("/")
def home():
    """initial endpoint for traits"""
    return jsonify({"results": "success"})


@trait.route("/<string:trait_name>/<string:dataset_name>")
def create_trait(trait_name, dataset_name):
    """endpoints for creating trait first should\
    call the endpoint for creating the trait only\
    trait  data is the  sample data"""

    trait_dataset = mock.Mock()  # xtodo should replace this with calling epoints
    trait_dataset.name = dataset_name

    trait_results = fetch_trait(dataset=trait_dataset, trait_name=trait_name)

    return jsonify(trait_results)


@trait.route("/trait_info/<string:trait_name>", methods=["POST"])
def fetch_trait_info(trait_name):
    """api endpoint for fetching the trait info \
    expects the trait and trait dataset to have\
    been created """
    data = request.get_json()

    trait_dataset = data["trait_dataset"]
    trait_data = data["trait"]
    _trait_name = trait_name  # should be used as key to return results

    database_instance = mock.Mock()

    results = get_trait_info_data(trait_dataset, trait_data, database_instance)

    return jsonify(results)
