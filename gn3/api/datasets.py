"""this module contains code for creating datasets"""
from flask import Blueprint
from flask import jsonify

from gn3.computations.datasets import create_dataset
from gn3.computations.datasets import get_traits_data
from gn3.experimental_db import database_connector


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
        "dataset": new_dataset
    }
    return jsonify(results)


@dataset.route("/fetch_traits_data/<dataset_name>/<dataset_type>")
def fetch_traits_data(dataset_name, dataset_type):
    """test fetch_traits_data/dataset_name/dataset_type"""
    # what actually brings speed issues in correlation
    # should fetch this
    trait_sample_ids = [4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15,
                        17, 18, 19, 20, 21, 22, 24, 25, 26, 28, 29, 30, 31,
                        35, 36, 37, 39, 98, 99, 100, 103, 487, 105, 106, 110, 115,
                        116, 117, 118, 119, 120, 919, 147,
                        121, 40, 41, 124, 125, 128, 135, 129, 130, 131,
                        132, 134, 138, 139, 140, 141, 142, 144,
                        145, 148, 149, 920, 922, 2, 3, 1, 1100]

    conn, _cursor = database_connector()
    results = get_traits_data(sample_ids=trait_sample_ids, database_instance=conn,
                              dataset_name=dataset_name, dataset_type=dataset_type)
    conn.close()

    return jsonify({"results": results})
