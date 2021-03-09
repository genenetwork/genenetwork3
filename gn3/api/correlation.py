"""Endpoints for computing correlation"""
import pickle

from flask import Blueprint
from flask import jsonify
from flask import request
from flask import g

# import pymysql

from sqlalchemy import create_engine
from gn3.correlation.correlation_computations import compute_correlation


SQL_URI = "mysql+pymysql://kabui:1234@localhost/db_webqtl"


correlation = Blueprint("correlation", __name__)


@correlation.before_request
def connect_db():
    """add connection to db method"""
    print("@app.before_request connect_db")
    db_connection = getattr(g, '_database', None)
    if db_connection is None:
        print("Get new database connector")
        g.db = g._database = create_engine(SQL_URI, encoding="latin1")


@correlation.route("/corr_compute", methods=["POST"])
def corr_compute_page():
    """api for doing  correlation"""

    # accepts both form and json data

    initial_start_vars = request.json

    corr_results = compute_correlation(init_start_vars=initial_start_vars)
    try:

        return pickle.dumps(corr_results)
    except Exception as error:  # pylint: disable=broad-except
        return jsonify({"error": str(error)})

