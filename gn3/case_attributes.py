"""Implement case-attribute manipulations."""
from functools import reduce

from MySQLdb.cursors import DictCursor
from flask import jsonify, Response, Blueprint, current_app

from gn3.db_utils import database_connection

caseattr = Blueprint("case-attribute", __name__)

@caseattr.route("/<int:inbredset_id>/names", methods=["GET"])
def inbredset_case_attribute_names(inbredset_id: int) -> Response:
    """Retrieve ALL case-attributes for a specific InbredSet group."""
    with (database_connection(current_app.config["SQL_URI"]) as conn,
          conn.cursor(cursorclass=DictCursor) as cursor):
        cursor.execute(
            "SELECT * FROM CaseAttribute WHERE InbredSetId=%(inbredset_id)s",
            {"inbredset_id": inbredset_id})
        return jsonify(tuple(dict(row) for row in cursor.fetchall()))

def __by_strain__(accumulator, item):
    attr = {item["CaseAttributeName"]: item["CaseAttributeValue"]}
    strain_name = item["StrainName"]
    if bool(accumulator.get(strain_name)):
        return {
            **accumulator,
            strain_name: {
                **accumulator[strain_name],
                "case-attributes": {
                    **accumulator[strain_name]["case-attributes"],
                    **attr
                }
            }
        }
    return {
        strain_name: {
            **{
                key: value for key,value in item.items()
                if key in ("StrainName", "StrainName2", "Symbol", "Alias")
            },
            "case-attributes": attr
        }
    }

@caseattr.route("/<int:inbredset_id>/values")
def inbredset_case_attribute_values(inbredset_id: int) -> Response:
    """Retrieve the group's (InbredSet's) case-attribute values."""
    with (database_connection(current_app.config["SQL_URI"]) as conn,
          conn.cursor(cursorclass=DictCursor) as cursor):
        cursor.execute(
            "SELECT ca.Name AS CaseAttributeName, "
            "caxrn.Value AS CaseAttributeValue, s.Name AS StrainName, "
            "s.Name2 AS StrainName2, s.Symbol, s.Alias "
            "FROM CaseAttribute AS ca "
            "INNER JOIN CaseAttributeXRefNew AS caxrn "
            "ON ca.CaseAttributeId=caxrn.CaseAttributeId "
            "INNER JOIN Strain AS s "
            "ON caxrn.StrainId=s.Id "
            "WHERE ca.InbredSetId=%(inbredset_id)s "
            "ORDER BY StrainName",
            {"inbredset_id": inbredset_id})
        return jsonify(tuple(
            reduce(__by_strain__, cursor.fetchall(), {}).values()))
