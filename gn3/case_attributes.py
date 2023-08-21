"""Implement case-attribute manipulations."""
from MySQLdb.cursors import DictCursor
from flask import jsonify, Response, Blueprint, current_app

from gn3.db_utils import database_connection

caseattr = Blueprint("case-attribute", __name__)

@caseattr.route("/<int:inbredset_id>", methods=["GET"])
def inbredset_case_attributes(inbredset_id: int) -> Response:
    """Retrieve ALL case-attributes for a specific InbredSet group."""
    with (database_connection(current_app.config["SQL_URI"]) as conn,
          conn.cursor(cursorclass=DictCursor) as cursor):
        cursor.execute(
            "SELECT * FROM CaseAttribute WHERE InbredSetId=%(inbredset_id)s",
            {"inbredset_id": inbredset_id})
        return jsonify(tuple(dict(row) for row in cursor.fetchall()))
