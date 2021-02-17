"""Endpoints for running the gemma cmd"""
from flask import Blueprint
from flask import jsonify

correlation = Blueprint("correlation", __name__)


@correlation.route("/")
def index() -> str:
    """Test endpoint"""
    return jsonify(result="hello world")
