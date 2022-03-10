from gn3.csvcmp import extract_strain_name
from typing import Any, Tuple, Union

import MySQLdb


_MAP = {
    "PublishData": ("StrainId", "Id", "value"),
    "PublishSE": ("StrainId", "DataId", "error"),
    "NStrain": ("StrainId", "DataId", "count"),
}


def __extract_actions(original_data: str,
                      updated_data: str,
                      csv_header: str) -> dict:
    original_data = original_data.strip().split(",")
    updated_data = updated_data.strip().split(",")
    csv_header = csv_header.strip().split(",")
    result = {
        "delete": {"data": [], "csv_header": []},
        "insert": {"data": [], "csv_header": []},
        "update": {"data": [], "csv_header": []},
    }
    for _o, _u, _h in zip(original_data, updated_data, csv_header):
        if _o == _u:  # No change
            continue
        elif _o and _u == "x":  # Deletion
            result["delete"]["data"].append(_o)
            result["delete"]["csv_header"].append(_h)
        elif _o == "x" and _u:  # Insert
            result["insert"]["data"].append(_u)
            result["insert"]["csv_header"].append(_h)
        elif _o and _u:  # Update
            result["update"]["data"].append(_u)
            result["update"]["csv_header"].append(_h)
    for key, val in result.items():
        if not val["data"]:
            result[key] = None
        else:
            result[key]["data"] = ",".join(result[key]["data"])
            result[key]["csv_header"] = ",".join(result[key]["csv_header"])
    return result


def get_trait_csv_sample_data(conn: Any,
                              trait_name: int, phenotype_id: int) -> str:
    """Fetch a trait and return it as a csv string"""
    __query = ("SELECT concat(st.Name, ',', ifnull(pd.value, 'x'), ',', "
               "ifnull(ps.error, 'x'), ',', ifnull(ns.count, 'x')) as 'Data' "
               ",ifnull(ca.Name, 'x') as 'CaseAttr', "
               "ifnull(cxref.value, 'x') as 'Value' "
               "FROM PublishFreeze pf "
               "JOIN PublishXRef px ON px.InbredSetId = pf.InbredSetId "
               "JOIN PublishData pd ON pd.Id = px.DataId "
               "JOIN Strain st ON pd.StrainId = st.Id "
               "LEFT JOIN PublishSE ps ON ps.DataId = pd.Id "
               "AND ps.StrainId = pd.StrainId "
               "LEFT JOIN NStrain ns ON ns.DataId = pd.Id "
               "AND ns.StrainId = pd.StrainId "
               "LEFT JOIN CaseAttributeXRefNew cxref ON "
               "(cxref.InbredSetId = px.InbredSetId AND "
               "cxref.StrainId = st.Id) "
               "LEFT JOIN CaseAttribute ca ON ca.Id = cxref.CaseAttributeId "
               "WHERE px.Id = %s AND px.PhenotypeId = %s ORDER BY st.Name")
    case_attr_columns = set()
    csv_data = {}
    with conn.cursor() as cursor:
        cursor.execute(__query, (trait_name, phenotype_id))
        for data in cursor.fetchall():
            if data[1] == "x":
                csv_data[data[0]] = None
            else:
                sample, case_attr, value = data[0], data[1], data[2]
                if not csv_data.get(sample):
                    csv_data[sample] = {}
                csv_data[sample][case_attr] = None if value == "x" else value
                case_attr_columns.add(case_attr)
        if not case_attr_columns:
            return ("Strain Name,Value,SE,Count\n" +
                    "\n".join(csv_data.keys()))
        else:
            columns = sorted(case_attr_columns)
            csv = ("Strain Name,Value,SE,Count," +
                   ",".join(columns) + "\n")
            for key, value in csv_data.items():
                if not value:
                    csv += (key + (len(case_attr_columns) * ",x") + "\n")
                else:
                    vals = [str(value.get(column, "x")) for column in columns]
                    csv += (key + "," + ",".join(vals) + "\n")
            return csv
    return "No Sample Data Found"


def get_sample_data_ids(conn: Any, publishxref_id: int,
                        phenotype_id: int,
                        strain_name: str) -> Tuple:
    strain_id, publishdata_id, inbredset_id = None, None, None
    with conn.cursor() as cursor:
        cursor.execute("SELECT st.id, pd.Id, pf.InbredSetId "
                       "FROM PublishData pd "
                       "JOIN Strain st ON pd.StrainId = st.Id "
                       "JOIN PublishXRef px ON px.DataId = pd.Id "
                       "JOIN PublishFreeze pf ON pf.InbredSetId "
                       "= px.InbredSetId WHERE px.Id = %s "
                       "AND px.PhenotypeId = %s AND st.Name = %s",
                       (publishxref_id, phenotype_id, strain_name))
        if _result := cursor.fetchone():
            strain_id, publishdata_id, inbredset_id = _result
        if not all([strain_id, publishdata_id, inbredset_id]):
            # Applies for data to be inserted:
            cursor.execute("SELECT DataId, InbredSetId FROM PublishXRef "
                           "WHERE Id = %s AND PhenotypeId = %s",
                           (publishxref_id, phenotype_id))
            publishdata_id, inbredset_id = cursor.fetchone()
            cursor.execute("SELECT Id FROM Strain WHERE Name = %s",
                           (strain_name,))
            strain_id = cursor.fetchone()
    return (strain_id, publishdata_id, inbredset_id)


def update_sample_data(conn: Any,  # pylint: disable=[R0913]
                       trait_name: str,
                       original_data: str,
                       updated_data: str,
                       csv_header: str,
                       phenotype_id: int) -> int:
    """Given the right parameters, update sample-data from the relevant
    table."""
    def __update_data(conn, table, value):
        if value and value != "x":
            with conn.cursor() as cursor:
                sub_query = (" = %s AND ".join(_MAP.get(table)[:2]) + " = %s")
                _val = _MAP.get(table)[-1]
                cursor.execute((f"UPDATE {table} SET {_val} = %s "
                                f"WHERE {sub_query}"),
                               (value, strain_id, data_id))
                return cursor.rowcount

    def __update_case_attribute(conn, value, strain_id,
                                case_attr, inbredset_id):
        if value != "x":
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE CaseAttributeXRefNew "
                    "SET Value = %s "
                    "WHERE StrainId = %s AND CaseAttributeId = "
                    "(SELECT CaseAttributeId FROM "
                    "CaseAttribute WHERE Name = %s) "
                    "AND InbredSetId = %s",
                    (value, strain_id, case_attr, inbredset_id))
                return cursor.rowcount
        return 0

    strain_id, data_id, inbredset_id = get_sample_data_ids(
        conn=conn, publishxref_id=trait_name,
        phenotype_id=phenotype_id,
        strain_name=extract_strain_name(csv_header, original_data))

    none_case_attrs = {
        "Strain Name": lambda x: 0,
        "Value": lambda x: __update_data(conn, "PublishData", x),
        "SE": lambda x: __update_data(conn, "PublishSE", x),
        "Count": lambda x: __update_data(conn, "NStrain", x),
    }
    count = 0
    try:
        __actions = __extract_actions(original_data=original_data,
                                      updated_data=updated_data,
                                      csv_header=csv_header)
        if __actions.get("update"):
            _csv_header = __actions["update"]["csv_header"]
            _data = __actions["update"]["data"]
            for header, value in zip(_csv_header.split(","),
                                     _data.split(",")):
                header = header.strip()
                value = value.strip()
                if header in none_case_attrs:
                    count += none_case_attrs.get(header)(value)
                else:
                    count += __update_case_attribute(
                        conn=conn,
                        value=none_case_attrs.get(header)(value),
                        strain_id=strain_id,
                        case_attr=header,
                        inbredset_id=inbredset_id)
        if __actions.get("delete"):
            _rowcount = delete_sample_data(
                conn=conn,
                trait_name=trait_name,
                data=__actions["delete"]["data"],
                csv_header=__actions["delete"]["csv_header"],
                phenotype_id=phenotype_id)
            if _rowcount:
                count += 1
        if __actions.get("insert"):
            _rowcount = insert_sample_data(
                conn=conn,
                trait_name=trait_name,
                data=__actions["insert"]["data"],
                csv_header=__actions["insert"]["csv_header"],
                phenotype_id=phenotype_id)
            if _rowcount:
                count += 1
    except Exception as e:  # pylint: disable=[C0103, W0612]
        conn.rollback()
        raise MySQLdb.Error
    conn.commit()
    return count


def delete_sample_data(conn: Any,
                       trait_name: str,
                       data: str,
                       csv_header: str,
                       phenotype_id: int) -> int:
    """Given the right parameters, delete sample-data from the relevant
    tables."""
    def __delete_data(conn, table):
        if value and value != "x":
            sub_query = (" = %s AND ".join(_MAP.get(table)[:2]) + " = %s")
            with conn.cursor() as cursor:
                cursor.execute((f"DELETE FROM {table} "
                                f"WHERE {sub_query}"),
                               (strain_id, data_id))
                return cursor.rowcount
        return 0

    def __delete_case_attribute(conn, strain_id,
                                case_attr, inbredset_id):
        if value != "x":
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM CaseAttributeXRefNew "
                    "WHERE StrainId = %s AND CaseAttributeId = "
                    "(SELECT CaseAttributeId FROM "
                    "CaseAttribute WHERE Name = %s) "
                    "AND InbredSetId = %s",
                    (strain_id, case_attr, inbredset_id))
                return cursor.rowcount
        return 0

    strain_id, data_id, inbredset_id = get_sample_data_ids(
        conn=conn, publishxref_id=trait_name,
        phenotype_id=phenotype_id,
        strain_name=extract_strain_name(csv_header, data))

    none_case_attrs = {
        "Strain Name": lambda: 0,
        "Value": lambda: __delete_data(conn, "PublishData"),
        "SE": lambda: __delete_data(conn, "PublishSE"),
        "Count": lambda: __delete_data(conn, "NStrain"),
    }
    count = 0

    try:
        for header, value in zip(csv_header.split(","), data.split(",")):
            header = header.strip()
            value = value.strip()
            if header in none_case_attrs:
                count += none_case_attrs.get(header)()
            else:
                count += __delete_case_attribute(
                    conn=conn,
                    strain_id=strain_id,
                    case_attr=header,
                    inbredset_id=inbredset_id)
    except Exception as e:  # pylint: disable=[C0103, W0612]
        conn.rollback()
        raise MySQLdb.Error
    conn.commit()
    return count


def insert_sample_data(conn: Any,  # pylint: disable=[R0913]
                       trait_name: str,
                       data: str,
                       csv_header: str,
                       phenotype_id: int) -> int:
    """Given the right parameters, insert sample-data to the relevant table.

    """
    def __insert_data(conn, table, value):
        if value and value != "x":
            with conn.cursor() as cursor:
                columns = ", ".join(_MAP.get(table))
                cursor.execute((f"INSERT INTO {table} "
                                f"({columns}) "
                                f"VALUES (%s, %s, %s)"),
                               (strain_id, data_id, value))
                return cursor.rowcount
        return 0

    def __insert_case_attribute(conn, case_attr, value):
        if value != "x":
            with conn.cursor() as cursor:
                cursor.execute("SELECT Id FROM "
                               "CaseAttribute WHERE Name = %s",
                               (case_attr,))
                if case_attr_id := cursor.fetchone():
                    case_attr_id = case_attr_id[0]
                cursor.execute("SELECT StrainId FROM "
                               "CaseAttributeXRefNew WHERE StrainId = %s "
                               "AND CaseAttributeId = %s "
                               "AND InbredSetId = %s",
                               (strain_id, case_attr_id, inbredset_id))
                if (not cursor.fetchone()) and case_attr_id:
                    cursor.execute(
                        "INSERT INTO CaseAttributeXRefNew "
                        "(StrainId, CaseAttributeId, Value, InbredSetId) "
                        "VALUES (%s, %s, %s, %s)",
                        (strain_id, case_attr_id, value, inbredset_id))
                    row_count = cursor.rowcount
                    return row_count
        return 0

    strain_id, data_id, inbredset_id = get_sample_data_ids(
        conn=conn, publishxref_id=trait_name,
        phenotype_id=phenotype_id,
        strain_name=extract_strain_name(csv_header, data))

    none_case_attrs = {
        "Strain Name": lambda _: 0,
        "Value": lambda x: __insert_data(conn, "PublishData", x),
        "SE": lambda x: __insert_data(conn, "PublishSE", x),
        "Count": lambda x: __insert_data(conn, "NStrain", x),
    }

    try:
        count = 0

        # Check if the data already exists:
        with conn.cursor() as cursor:
            cursor.execute(
                    "SELECT Id FROM PublishData where Id = %s "
                    "AND StrainId = %s",
                    (data_id, strain_id))
        if cursor.fetchone():  # Data already exists
            return count

        for header, value in zip(csv_header.split(","), data.split(",")):
            header = header.strip()
            value = value.strip()
            if header in none_case_attrs:
                count += none_case_attrs.get(header)(value)
            else:
                count += __insert_case_attribute(
                    conn=conn,
                    case_attr=header,
                    value=value)
        return count
    except Exception as e:  # pylint: disable=[C0103, W0612]
        conn.rollback()
        raise MySQLdb.Error
