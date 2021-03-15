"""Endpoints for computing correlation"""
import time
from flask import Blueprint
from flask import jsonify
from flask import request
from flask import g
from sqlalchemy import create_engine

from default_settings import SQL_URI
from gn3.correlation.correlation_computations import compute_correlation

correlation = Blueprint("correlation", __name__)


# xtodo implement neat db setup
@correlation.before_request
def connect_db():
    """add connection to db method"""
    print("@app.before_request connect_db")
    db_connection = getattr(g, '_database', None)
    if db_connection is None:
        print("Get new database connector")
        g.db = g._database = create_engine(SQL_URI, encoding="latin1")

    g.initial_time = time.time()


@correlation.route("/corr_compute", methods=["POST"])
def corr_compute_page():
    """api for doing  correlation"""

    correlation_input = request.json

    if correlation_input is None:
        return jsonify({"error": str("Bad request")}), 400

    try:
        corr_results = compute_correlation(
            correlation_input_data=correlation_input)

    except Exception as error:  # pylint: disable=broad-except
        return jsonify({"error": str(error)})

    return {"correlation_results": corr_results}
