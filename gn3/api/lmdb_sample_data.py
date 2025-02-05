"""API endpoint for retrieving sample data from LMDB storage"""
import hashlib
from pathlib import Path

import lmdb
from flask import Blueprint, current_app, jsonify

lmdb_sample_data = Blueprint("lmdb_sample_data", __name__)


@lmdb_sample_data.route("/sample-data/<string:dataset>/<int:trait_id>", methods=["GET"])
def get_sample_data(dataset: str, trait_id: int):
    """Retrieve sample data from LMDB for a given dataset and trait.

    Path Parameters:
        dataset: The name of the dataset
        trait_id: The ID of the trait

    Returns:
        JSON object mapping sample IDs to their values
    """
    checksum = hashlib.md5(
        f"{dataset}-{trait_id}".encode()
    ).hexdigest()

    db_path = Path(current_app.config["LMDB_DATA_PATH"]) / checksum
    if not db_path.exists():
        return jsonify(error="No data found for given dataset and trait"), 404
    try:
        with lmdb.open(str(db_path), max_dbs=15, readonly=True) as env:
            data = {}
            with env.begin(write=False) as txn:
                cursor = txn.cursor()
                for key, value in cursor:
                    data[key.decode()] = float(value.decode())

            return jsonify(data)

    except lmdb.Error as err:
        return jsonify(error=f"LMDB error: {str(err)}"), 500
