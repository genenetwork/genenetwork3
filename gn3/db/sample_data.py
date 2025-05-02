"""Module containing functions that work with sample data"""
from typing import Any, Tuple, Dict

import MySQLdb

from gn3.csvcmp import extract_strain_name
from gn3.csvcmp import parse_csv_column

_MAP = {
    "ProbeSetData": ("StrainId", "Id", "value"),
    "PublishData": ("StrainId", "Id", "value"),
    "ProbeSetSE": ("StrainId", "DataId", "error"),
    "PublishSE": ("StrainId", "DataId", "error"),
    "NStrain": ("StrainId", "DataId", "count"),
}


def __extract_actions(
    original_data: str, updated_data: str, csv_header: str
) -> Dict:
    """Return a dictionary containing elements that need to be deleted, inserted,
    or updated.

    """
    result: Dict[str, Any] = {
        "delete": {"data": [], "csv_header": []},
        "insert": {"data": [], "csv_header": []},
        "update": {"data": [], "csv_header": []},
    }
    strain_name = ""
    for _o, _u, _h in zip(
        original_data.strip().split(","),
        updated_data.strip().split(","),
        csv_header.strip().split(","),
    ):
        if _h == "Strain Name":
            strain_name = _o
        if _o == _u:  # No change
            continue
        if _o and _u == "x":  # Deletion
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
            result[key]["data"] = f"{strain_name}," + ",".join(
                result[key]["data"]
            )
            result[key]["csv_header"] = "Strain Name," + ",".join(
                result[key]["csv_header"]
            )
    return result

def get_mrna_sample_data(
    conn: Any, probeset_id: int, dataset_name: str, probeset_name: str = None
) -> Dict:
    """Fetch a mRNA Assay (ProbeSet in the DB) trait's sample data and return it as a dict"""
    with conn.cursor() as cursor:
        if probeset_name:
            cursor.execute("""
    SELECT st.Name, ifnull(psd.value, 'x'), ifnull(psse.error, 'x'), ifnull(ns.count, 'x')
    FROM ProbeSetFreeze psf
        JOIN ProbeSetXRef psx ON psx.ProbeSetFreezeId = psf.Id
        JOIN ProbeSet ps ON ps.Id = psx.ProbeSetId
        JOIN ProbeSetData psd ON psd.Id = psx.DataId
        JOIN Strain st ON psd.StrainId = st.Id
        LEFT JOIN ProbeSetSE psse ON psse.DataId = psd.Id AND psse.StrainId = psd.StrainId
        LEFT JOIN NStrain ns ON ns.DataId = psd.Id AND ns.StrainId = psd.StrainId
    WHERE ps.Name = %s AND psf.Name= %s""", (probeset_name, dataset_name))
        else:
            cursor.execute("""
    SELECT st.Name, ifnull(psd.value, 'x'), ifnull(psse.error, 'x'), ifnull(ns.count, 'x')
    FROM ProbeSetFreeze psf
        JOIN ProbeSetXRef psx ON psx.ProbeSetFreezeId = psf.Id
        JOIN ProbeSet ps ON ps.Id = psx.ProbeSetId
        JOIN ProbeSetData psd ON psd.Id = psx.DataId
        JOIN Strain st ON psd.StrainId = st.Id
        LEFT JOIN ProbeSetSE psse ON psse.DataId = psd.Id AND psse.StrainId = psd.StrainId
        LEFT JOIN NStrain ns ON ns.DataId = psd.Id AND ns.StrainId = psd.StrainId
    WHERE ps.Id = %s AND psf.Name= %s""", (probeset_id, dataset_name))

        sample_data = {}
        for data in cursor.fetchall():
            sample, value, error, n_cases = data
            sample_data[sample] = {
                'value': value,
                'error': error,
                'n_cases': n_cases
            }

        return sample_data

def get_mrna_csv_sample_data(
    conn: Any, probeset_id: str, dataset_name: str, sample_list: list
) -> str:
    """Fetch a mRNA Assay (ProbeSet in DB) trait and return it as a csv string"""
    with conn.cursor() as cursor:
        cursor.execute("""
SELECT DISTINCT st.Name, concat(st.Name, ',', ifnull(psd.value, 'x'), ',',
    ifnull(psse.error, 'x'), ',', ifnull(ns.count, 'x')) AS 'Data'
FROM ProbeSetFreeze psf
    JOIN ProbeSetXRef psx ON psx.ProbeSetFreezeId = psf.Id
    JOIN ProbeSet ps ON ps.Id = psx.ProbeSetId
    JOIN ProbeSetData psd ON psd.Id = psx.DataId
    JOIN Strain st ON psd.StrainId = st.Id
    LEFT JOIN ProbeSetSE psse ON psse.DataId = psd.Id AND psse.StrainId = psd.StrainId
    LEFT JOIN NStrain ns ON ns.DataId = psd.Id AND ns.StrainId = psd.StrainId
WHERE ps.Id = %s AND psf.Name= %s""", (probeset_id, dataset_name))

        if not (data := cursor.fetchall()):
            return "No Sample Data Found"

        # Get list of samples with data in the DB
        existing_samples = [el[0] for el in data]

        trait_csv = ["Strain Name,Value,SE,Count"]
        for sample in sample_list:
            if sample in existing_samples:
                trait_csv.append(data[existing_samples.index(sample)][1])
            else:
                trait_csv.append(sample + ",x,x,x")

        return "\n".join(trait_csv)

def get_pheno_sample_data(
    conn: Any, trait_name: int, phenotype_id: int, group_id: int = None
) -> Dict:
    """Fetch a phenotype (Publish in the DB) trait's sample data and return it as a dict"""
    with conn.cursor() as cursor:
        if group_id:
            cursor.execute("""
    SELECT st.Name, ifnull(ROUND(pd.value, 2), 'x'), ifnull(ROUND(ps.error, 3), 'x'), ifnull(ns.count, 'x')
    FROM PublishFreeze pf JOIN PublishXRef px ON px.InbredSetId = pf.InbredSetId
        JOIN PublishData pd ON pd.Id = px.DataId JOIN Strain st ON pd.StrainId = st.Id
        LEFT JOIN PublishSE ps ON ps.DataId = pd.Id AND ps.StrainId = pd.StrainId
        LEFT JOIN NStrain ns ON ns.DataId = pd.Id AND ns.StrainId = pd.StrainId
    WHERE px.Id = %s AND px.InbredSetId = %s
    ORDER BY st.Name""", (trait_name, group_id))
        else:
            cursor.execute("""
    SELECT st.Name, ifnull(pd.value, 'x'), ifnull(ps.error, 'x'), ifnull(ns.count, 'x')
    FROM PublishFreeze pf JOIN PublishXRef px ON px.InbredSetId = pf.InbredSetId
        JOIN PublishData pd ON pd.Id = px.DataId JOIN Strain st ON pd.StrainId = st.Id
        LEFT JOIN PublishSE ps ON ps.DataId = pd.Id AND ps.StrainId = pd.StrainId
        LEFT JOIN NStrain ns ON ns.DataId = pd.Id AND ns.StrainId = pd.StrainId
    WHERE px.Id = %s AND px.PhenotypeId = %s
    ORDER BY st.Name""", (trait_name, phenotype_id))

        sample_data = {}
        for data in cursor.fetchall():
            sample, value, error, n_cases = data
            sample_data[sample] = {
                'value': value,
                'error': error,
                'n_cases': n_cases
            }

        return sample_data

def get_pheno_csv_sample_data(
    conn: Any, trait_name: int, group_id: int, sample_list: list
) -> str:
    """Fetch a phenotype (Publish in DB) trait and return it as a csv string"""
    with conn.cursor() as cursor:
        cursor.execute("""
SELECT DISTINCT st.Name, concat(st.Name, ',', ifnull(pd.value, 'x'), ',',
ifnull(ps.error, 'x'), ',', ifnull(ns.count, 'x')) AS 'Data'
FROM PublishFreeze pf JOIN PublishXRef px ON px.InbredSetId = pf.InbredSetId
     JOIN PublishData pd ON pd.Id = px.DataId JOIN Strain st ON pd.StrainId = st.Id
     LEFT JOIN PublishSE ps ON ps.DataId = pd.Id AND ps.StrainId = pd.StrainId
     LEFT JOIN NStrain ns ON ns.DataId = pd.Id AND ns.StrainId = pd.StrainId
WHERE px.Id = %s AND px.InbredSetId = %s ORDER BY st.Name""",
                       (trait_name, group_id))
        if not (data := cursor.fetchall()):
            return "No Sample Data Found"

        # Get list of samples with data in the DB
        existing_samples = [el[0] for el in data]

        trait_csv = ["Strain Name,Value,SE,Count"]
        for sample in sample_list:
            if sample in existing_samples:
                trait_csv.append(data[existing_samples.index(sample)][1])
            else:
                trait_csv.append(sample + ",x,x,x")

        return "\n".join(trait_csv)

def get_mrna_sample_data_ids(
    conn: Any, probeset_id: int, dataset_name: str, strain_name: str
) -> Tuple:
    """Get the strain_id, probesetdata_id and inbredset_id for a given strain"""
    strain_id, probesetdata_id, inbredset_id = None, None, None
    with conn.cursor() as cursor:
        cursor.execute("""
SELECT st.id, psd.Id, pf.InbredSetId
FROM ProbeFreeze pf
    JOIN ProbeSetFreeze psf ON psf.ProbeFreezeId = pf.Id
    JOIN ProbeSetXRef psx ON psx.ProbeSetFreezeId = psf.Id
    JOIN ProbeSet ps ON ps.Id = psx.ProbeSetId
    JOIN ProbeSetData psd ON psd.Id = psx.DataId
    JOIN Strain st ON psd.StrainId = st.Id
    LEFT JOIN ProbeSetSE psse ON psse.DataId = psd.Id AND psse.StrainId = psd.StrainId
    LEFT JOIN NStrain ns ON ns.DataId = psd.Id AND ns.StrainId = psd.StrainId
WHERE ps.Id = %s AND psf.Name= %s AND st.Name = %s""", (probeset_id, dataset_name, strain_name))
        if _result := cursor.fetchone():
            strain_id, probesetdata_id, inbredset_id = _result
        if not all([strain_id, probesetdata_id, inbredset_id]):
            # Applies for data to be inserted:
            cursor.execute("""
SELECT psx.DataId, pf.InbredSetId
FROM ProbeFreeze pf
    JOIN ProbeSetFreeze psf ON psf.ProbeFreezeId = pf.Id
    JOIN ProbeSetXRef psx ON psx.ProbeSetFreezeId = psf.Id
WHERE psx.ProbeSetId = %s AND
      psf.Name = %s""", (probeset_id, dataset_name))

            probesetdata_id, inbredset_id = cursor.fetchone()
            cursor.execute(
                "SELECT Id FROM Strain WHERE Name = %s", (strain_name,)
            )
            strain_id = cursor.fetchone()[0]
    return (strain_id, probesetdata_id, inbredset_id)

def get_pheno_sample_data_ids(
    conn: Any, publishxref_id: int, phenotype_id: int, strain_name: str
) -> Tuple:
    """Get the strain_id, publishdata_id and inbredset_id for a given strain"""
    strain_id, publishdata_id, inbredset_id = None, None, None
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT st.id, pd.Id, pf.InbredSetId "
            "FROM PublishData pd "
            "JOIN Strain st ON pd.StrainId = st.Id "
            "JOIN PublishXRef px ON px.DataId = pd.Id "
            "JOIN PublishFreeze pf ON pf.InbredSetId "
            "= px.InbredSetId WHERE px.Id = %s "
            "AND px.PhenotypeId = %s AND st.Name = %s",
            (publishxref_id, phenotype_id, strain_name),
        )
        if _result := cursor.fetchone():
            strain_id, publishdata_id, inbredset_id = _result
        if not all([strain_id, publishdata_id, inbredset_id]):
            # Applies for data to be inserted:
            cursor.execute(
                "SELECT DataId, InbredSetId FROM PublishXRef "
                "WHERE Id = %s AND PhenotypeId = %s",
                (publishxref_id, phenotype_id),
            )
            publishdata_id, inbredset_id = cursor.fetchone()
            cursor.execute(
                "SELECT Id FROM Strain WHERE Name = %s", (strain_name,)
            )
            strain_id = cursor.fetchone()[0]
    return (strain_id, publishdata_id, inbredset_id)


# pylint: disable=[R0913, R0914]
def update_sample_data(
    conn: Any,
    original_data: str,
    updated_data: str,
    csv_header: str,
    trait_info: dict
) -> int:
    """Given the right parameters, update sample-data from the relevant
    table."""

    def __update_data(conn, table, value):
        if value and value != "x":
            with conn.cursor() as cursor:
                sub_query = " = %s AND ".join(_MAP.get(table)[:2]) + " = %s"
                _val = _MAP.get(table)[-1]
                cursor.execute(
                    (f"UPDATE {table} SET {_val} = %s " f"WHERE {sub_query}"),
                    (value, strain_id, data_id),
                )
                conn.commit()
                return cursor.rowcount
        return 0

    def __update_case_attribute(
        conn, value, strain_id, case_attr, inbredset_id
    ):
        if value != "x":
            (id_, name) = parse_csv_column(case_attr)
            with conn.cursor() as cursor:
                if id_:
                    cursor.execute(
                        "UPDATE CaseAttributeXRefNew "
                        "SET Value = %s "
                        "WHERE StrainId = %s AND CaseAttributeId = %s "
                        "AND InbredSetId = %s",
                        (value, strain_id, id_, inbredset_id),
                    )
                else:
                    cursor.execute(
                        "UPDATE CaseAttributeXRefNew "
                        "SET Value = %s "
                        "WHERE StrainId = %s AND CaseAttributeId = "
                        "(SELECT CaseAttributeId FROM "
                        "CaseAttribute WHERE Name = %s) "
                        "AND InbredSetId = %s",
                        (value, strain_id, name, inbredset_id),
                    )
                conn.commit()
                return cursor.rowcount
        return 0

    if 'probeset_id' in trait_info and 'dataset_name' in trait_info: # If ProbeSet/mRNA Assay trait
        probeset_id, dataset_name = trait_info['probeset_id'], trait_info['dataset_name']
        data_type = "mrna"
    else: # If Publish/phenotype trait
        trait_name, phenotype_id = trait_info['trait_name'], trait_info['phenotype_id']
        data_type = "pheno"

    if data_type == "mrna":
        strain_id, data_id, inbredset_id = get_mrna_sample_data_ids(
            conn=conn,
            probeset_id=int(probeset_id),# pylint: disable=[possibly-used-before-assignment]
            dataset_name=dataset_name,# pylint: disable=[possibly-used-before-assignment]
            strain_name=extract_strain_name(csv_header, original_data),
        )
        none_case_attrs = {
            "Strain Name": lambda x: 0,
            "Value": lambda x: __update_data(conn, "ProbeSetData", x),
            "SE": lambda x: __update_data(conn, "ProbeSetSE", x),
            "Count": lambda x: __update_data(conn, "NStrain", x),
        }
    else:
        strain_id, data_id, inbredset_id = get_pheno_sample_data_ids(
            conn=conn,
            publishxref_id=int(trait_name),# pylint: disable=[possibly-used-before-assignment]
            phenotype_id=phenotype_id,# pylint: disable=[possibly-used-before-assignment]
            strain_name=extract_strain_name(csv_header, original_data),
        )
        none_case_attrs = {
            "Strain Name": lambda x: 0,
            "Value": lambda x: __update_data(conn, "PublishData", x),
            "SE": lambda x: __update_data(conn, "PublishSE", x),
            "Count": lambda x: __update_data(conn, "NStrain", x),
        }

    count = 0
    # try:
    __actions = __extract_actions(
        original_data=original_data,
        updated_data=updated_data,
        csv_header=csv_header,
    )

    if __actions.get("update"):
        _csv_header = __actions["update"]["csv_header"]
        _data = __actions["update"]["data"]
        # pylint: disable=[E1101]
        for header, value in zip(_csv_header.split(","), _data.split(",")):
            header = header.strip()
            value = value.strip()
            if header in none_case_attrs:
                count += none_case_attrs[header](value)
            else:
                count += __update_case_attribute(
                    conn=conn,
                    value=value,
                    strain_id=strain_id,
                    case_attr=header,
                    inbredset_id=inbredset_id,
                )

    if __actions.get("delete"):
        _rowcount = delete_sample_data(
            conn=conn,
            data=__actions["delete"]["data"],
            csv_header=__actions["delete"]["csv_header"],
            trait_info=trait_info
        )
        if _rowcount:
            count += 1
    if __actions.get("insert"):
        _rowcount = insert_sample_data(
            conn=conn,
            data=__actions["insert"]["data"],
            csv_header=__actions["insert"]["csv_header"],
            trait_info=trait_info
        )
        if _rowcount:
            count += 1
    # except Exception as _e:
    #     raise MySQLdb.Error(_e) from _e
    return count

def delete_sample_data(
    conn: Any, data: str, csv_header: str, trait_info: dict
) -> int:
    """Given the right parameters, delete sample-data from the relevant
    tables."""

    def __delete_data(conn, table):
        sub_query = " = %s AND ".join(_MAP.get(table)[:2]) + " = %s"
        with conn.cursor() as cursor:
            cursor.execute(
                (f"DELETE FROM {table} " f"WHERE {sub_query}"),
                (strain_id, data_id),
            )
            conn.commit()
            return cursor.rowcount

    def __delete_case_attribute(conn, strain_id, case_attr, inbredset_id):
        with conn.cursor() as cursor:
            (id_, name) = parse_csv_column(case_attr)
            if id_:
                cursor.execute(
                    "DELETE FROM CaseAttributeXRefNew "
                    "WHERE StrainId = %s AND CaseAttributeId = %s "
                    "AND InbredSetId = %s",
                    (strain_id, id_, inbredset_id),
                )
            else:
                cursor.execute(
                    "DELETE FROM CaseAttributeXRefNew "
                    "WHERE StrainId = %s AND CaseAttributeId = "
                    "(SELECT CaseAttributeId FROM "
                    "CaseAttribute WHERE Name = %s) "
                    "AND InbredSetId = %s",
                    (strain_id, name, inbredset_id),
                )
            conn.commit()
            return cursor.rowcount

    if 'probeset_id' in trait_info and 'dataset_name' in trait_info: # If ProbeSet/mRNA Assay trait
        probeset_id, dataset_name = trait_info['probeset_id'], trait_info['dataset_name']
        data_type = "mrna"
    else: # If Publish/phenotype trait
        trait_name, phenotype_id = trait_info['trait_name'], trait_info['phenotype_id']
        data_type = "pheno"

    if data_type == "mrna":
        strain_id, data_id, inbredset_id = get_mrna_sample_data_ids(
            conn=conn,
            probeset_id=int(probeset_id),# pylint: disable=[possibly-used-before-assignment]
            dataset_name=dataset_name,# pylint: disable=[possibly-used-before-assignment]
            strain_name=extract_strain_name(csv_header, data),
        )
        none_case_attrs: Dict[str, Any] = {
            "Strain Name": lambda: 0,
            "Value": lambda: __delete_data(conn, "ProbeSetData"),
            "SE": lambda: __delete_data(conn, "ProbeSetSE"),
            "Count": lambda: __delete_data(conn, "NStrain"),
        }
    else:
        strain_id, data_id, inbredset_id = get_pheno_sample_data_ids(
            conn=conn,
            publishxref_id=int(trait_name),# pylint: disable=[possibly-used-before-assignment]
            phenotype_id=phenotype_id,# pylint: disable=[possibly-used-before-assignment]
            strain_name=extract_strain_name(csv_header, data),
        )
        none_case_attrs = {
            "Strain Name": lambda: 0,
            "Value": lambda: __delete_data(conn, "PublishData"),
            "SE": lambda: __delete_data(conn, "PublishSE"),
            "Count": lambda: __delete_data(conn, "NStrain"),
        }

    count = 0

    try:
        for header in csv_header.split(","):
            header = header.strip()
            if header in none_case_attrs:
                count += none_case_attrs[header]()
            else:
                count += __delete_case_attribute(
                    conn=conn,
                    strain_id=strain_id,
                    case_attr=header,
                    inbredset_id=inbredset_id,
                )
    except Exception as _e:
        raise MySQLdb.Error(_e) from _e
    return count

# pylint: disable=[R0913, R0914]
def insert_sample_data(
    conn: Any, data: str, csv_header: str, trait_info: dict
) -> int:
    """Given the right parameters, insert sample-data to the relevant table."""

    def __insert_data(conn, table, value):
        if value and value != "x":
            with conn.cursor() as cursor:
                columns = ", ".join(_MAP.get(table))
                cursor.execute(
                    (
                        f"INSERT INTO {table} "
                        f"({columns}) "
                        f"VALUES (%s, %s, %s)"
                    ),
                    (strain_id, data_id, value),
                )
                conn.commit()
                return cursor.rowcount
        return 0

    def __insert_case_attribute(conn, case_attr, value):
        if value != "x":
            with conn.cursor() as cursor:
                (id_, name) = parse_csv_column(case_attr)
                if not id_:
                    cursor.execute(
                        "SELECT Id FROM CaseAttribute WHERE Name = %s",
                        (name,),
                    )
                    if case_attr_id := cursor.fetchone():
                        id_ = case_attr_id[0]

                cursor.execute(
                    "SELECT StrainId FROM "
                    "CaseAttributeXRefNew WHERE StrainId = %s "
                    "AND CaseAttributeId = %s "
                    "AND InbredSetId = %s",
                    (strain_id, id_, inbredset_id),
                )
                if (not cursor.fetchone()) and id_:
                    cursor.execute(
                        "INSERT INTO CaseAttributeXRefNew "
                        "(StrainId, CaseAttributeId, Value, InbredSetId) "
                        "VALUES (%s, %s, %s, %s)",
                        (strain_id, id_, value, inbredset_id),
                    )
                    row_count = cursor.rowcount
                    conn.commit()
                    return row_count
                conn.commit()
        return 0

    if 'probeset_id' in trait_info and 'dataset_name' in trait_info: # If ProbeSet/mRNA Assay trait
        probeset_id, dataset_name = trait_info['probeset_id'], trait_info['dataset_name']
        data_type = "mrna"
    else: # If Publish/phenotype trait
        trait_name, phenotype_id = trait_info['trait_name'], trait_info['phenotype_id']
        data_type = "pheno"

    if data_type == "mrna":
        strain_id, data_id, inbredset_id = get_mrna_sample_data_ids(
            conn=conn,
            probeset_id=int(probeset_id),# pylint: disable=[possibly-used-before-assignment]
            dataset_name=dataset_name,# pylint: disable=[possibly-used-before-assignment]
            strain_name=extract_strain_name(csv_header, data),
        )
        none_case_attrs = {
            "Strain Name": lambda _: 0,
            "Value": lambda x: __insert_data(conn, "ProbeSetData", x),
            "SE": lambda x: __insert_data(conn, "ProbeSetSE", x),
            "Count": lambda x: __insert_data(conn, "NStrain", x),
        }
    else:
        strain_id, data_id, inbredset_id = get_pheno_sample_data_ids(
            conn=conn,
            publishxref_id=int(trait_name),# pylint: disable=[possibly-used-before-assignment]
            phenotype_id=phenotype_id,# pylint: disable=[possibly-used-before-assignment]
            strain_name=extract_strain_name(csv_header, data),
        )
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
            if data_type == "mrna":
                cursor.execute(
                    "SELECT Id FROM ProbeSetData where Id = %s "
                    "AND StrainId = %s",
                    (data_id, strain_id))
            else:
                cursor.execute(
                    "SELECT Id FROM PublishData where Id = %s "
                    "AND StrainId = %s",
                    (data_id, strain_id))
            data_exists = cursor.fetchone()

        if data_exists:  # Data already exists
            return count

        for header, value in zip(csv_header.split(","), data.split(",")):
            header = header.strip()
            value = value.strip()
            if header in none_case_attrs:
                count += none_case_attrs[header](value)
            else:
                count += __insert_case_attribute(
                    conn=conn, case_attr=header, value=value
                )
        return count
    except Exception as _e:
        raise MySQLdb.Error(_e) from _e
