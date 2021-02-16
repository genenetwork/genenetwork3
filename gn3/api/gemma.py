"""Endpoints for running the gemma cmd"""
from flask import Blueprint
from flask import jsonify

gemma = Blueprint("gemma", __name__)


@gemma.route("/")
def index() -> str:
    """Test endpoint"""
    return jsonify(result="hello world")
