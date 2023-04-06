"""API for data used to generate menus"""

from flask import jsonify, Blueprint, current_app

from gn3.db.menu import gen_dropdown_json
from gn3.db_utils import database_connection

menu = Blueprint("menu", __name__)

@menu.route("/generate/json")
def generate_json():
    """Get the menu in the JSON format"""
    with database_connection(current_app.config["SQL_URI"]) as conn:
        return jsonify(gen_dropdown_json(conn))
