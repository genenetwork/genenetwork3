"""Endpoints used for data entry"""
from flask import Blueprint
from flask import jsonify


data_entry = Blueprint("data_entry", __name__)


@data_entry.route("/phenotype", methods=["POST"],
                  strict_slashes=False)
def load_phenotype():
    """Load the phenotype"""
    return jsonify("Pass")


@data_entry.route("/genotype", methods=["POST"],
                  strict_slashes=False)
def load_genotype():
    """Load the genotype"""
    return jsonify("Pass")
