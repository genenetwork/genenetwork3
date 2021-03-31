"""this module contains code for creating datasets"""
from flask import Blueprint
from flask import jsonify

from gn3.computations.datasets import create_dataset


dataset = Blueprint("dataset", __name__)


@dataset.route("/")
def dataset_home():
    """initial test endpont for dataset"""
    return jsonify({"results": "ok"})


@dataset.route("/create/<dataset_name>/")
@dataset.route("/create/<dataset_name>/<dataset_type>")
def create_dataset_api(dataset_name, dataset_type=None):
    """Test api/create/dataset/<dataset_name>/<dataset_type>"""

    new_dataset = create_dataset(
        dataset_type=dataset_type, dataset_name=dataset_name)

    results = {
        "dataset":new_dataset
    }
    return jsonify(results)
