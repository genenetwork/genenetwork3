"""Endpoints for running the gemma cmd"""
from flask import Blueprint

gemma = Blueprint("gemma", __name__)


@gemma.route("/")
def index() -> str:
    """Test endpoint"""
    return "hello world"
