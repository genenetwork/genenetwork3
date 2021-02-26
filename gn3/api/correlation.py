"""Endpoints for computing correlation"""
import json
from flask import Blueprint
from flask import jsonify
from flask import request
import pymysql
from flask import g
from sqlalchemy import create_engine

from gn3.correlation.correlation_computations import get_loading_page_data
from gn3.correlation.correlation_computations import compute_correlation



SQL_URI = "mysql+pymysql://kabui:1234@localhost/db_webqtl"

# from database import db



correlation = Blueprint("correlation", __name__)



@correlation.before_request
def connect_db():
    print("@app.before_request connect_db")
    db = getattr(g, '_database', None)
    if db is None:
        print("Get new database connector")
        g.db = g._database = create_engine(SQL_URI, encoding="latin1")
        print(g.db)


@correlation.route("/corr_compute", methods=["POST"])
def corr_compute_page():
    """api for doing  correlation"""

    print(g.db)

    initial_start_vars = request.json

    corr_results = compute_correlation(init_start_vars=initial_start_vars)
    try:
        corr_results = json.loads(json.dumps(
            corr_results, default=lambda o: o.__dict__))

        return corr_results
    except Exception as e:
        return jsonify({"error": str(e)})
