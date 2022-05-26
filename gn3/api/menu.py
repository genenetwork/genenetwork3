"""API for data used to generate menus"""

from flask import jsonify, Blueprint

from gn3.db.menu import gen_dropdown_json
from gn3.db_utils import database_connector

menu = Blueprint("menu", __name__)

@menu.route("/generate/json")
def generate_json():
    """Get the menu in the JSON format"""
    with database_connector() as conn:
        return jsonify(gen_dropdown_json(conn))
