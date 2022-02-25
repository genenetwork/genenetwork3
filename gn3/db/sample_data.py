from typing import Any, Tuple, Union

import MySQLdb

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


def update_sample_data(conn: Any,  # pylint: disable=[R0913]
                       trait_name: str,
                       strain_name: str,
                       phenotype_id: int,
                       value: Union[int, float, str],
                       error: Union[int, float, str],
                       count: Union[int, str]):
    """Given the right parameters, update sample-data from the relevant
    table."""
    strain_id, data_id = "", ""

    with conn.cursor() as cursor:
        cursor.execute(
            ("SELECT Strain.Id, PublishData.Id FROM "
             "(PublishData, Strain, PublishXRef, PublishFreeze) "
             "LEFT JOIN PublishSE ON "
             "(PublishSE.DataId = PublishData.Id AND "
             "PublishSE.StrainId = PublishData.StrainId) "
             "LEFT JOIN NStrain ON "
             "(NStrain.DataId = PublishData.Id AND "
             "NStrain.StrainId = PublishData.StrainId) "
             "WHERE PublishXRef.InbredSetId = "
             "PublishFreeze.InbredSetId AND "
             "PublishData.Id = PublishXRef.DataId AND "
             "PublishXRef.Id = %s AND "
             "PublishXRef.PhenotypeId = %s "
             "AND PublishData.StrainId = Strain.Id "
             "AND Strain.Name = \"%s\"") % (trait_name,
                                            phenotype_id,
                                            str(strain_name)))
        strain_id, data_id = cursor.fetchone()
    updated_published_data: int = 0
    updated_se_data: int = 0
    updated_n_strains: int = 0

    with conn.cursor() as cursor:
        # Update the PublishData table
        if value == "x":
            cursor.execute(("DELETE FROM PublishData "
                            "WHERE StrainId = %s AND Id = %s")
                           % (strain_id, data_id))
            updated_published_data = cursor.rowcount
        else:
            cursor.execute(("UPDATE PublishData SET value = %s "
                        "WHERE StrainId = %s AND Id = %s"),
                       (value, strain_id, data_id))
            updated_published_data = cursor.rowcount

            if not updated_published_data:
                cursor.execute(
                    "SELECT * FROM "
                    "PublishData WHERE StrainId = "
                    "%s AND Id = %s" % (strain_id, data_id))
                if not cursor.fetchone():
                    cursor.execute(("INSERT INTO PublishData (Id, StrainId, "
                                    " value) VALUES (%s, %s, %s)") %
                                   (data_id, strain_id, value))
                    updated_published_data = cursor.rowcount

        # Update the PublishSE table
        if error == "x":
            cursor.execute(("DELETE FROM PublishSE "
                            "WHERE StrainId = %s AND DataId = %s") %
                           (strain_id, data_id))
            updated_se_data = cursor.rowcount
        else:
            cursor.execute(("UPDATE PublishSE SET error = %s "
                            "WHERE StrainId = %s AND DataId = %s"),
                           (None if error == "x" else error,
                            strain_id, data_id))
            updated_se_data = cursor.rowcount
            if not updated_se_data:
                cursor.execute(
                        "SELECT * FROM "
                        "PublishSE WHERE StrainId = "
                        "%s AND DataId = %s" % (strain_id, data_id))
                if not cursor.fetchone():
                    cursor.execute(("INSERT INTO PublishSE (StrainId, DataId, "
                                    " error) VALUES (%s, %s, %s)") %
                                   (strain_id, data_id,
                                    None if error == "x" else error))
                    updated_se_data = cursor.rowcount

        # Update the NStrain table
        if count == "x":
            cursor.execute(("DELETE FROM NStrain "
                                "WHERE StrainId = %s AND DataId = %s" %
                                (strain_id, data_id)))
            updated_n_strains = cursor.rowcount
        else:
            cursor.execute(("UPDATE NStrain SET count = %s "
                            "WHERE StrainId = %s AND DataId = %s"),
                           (count, strain_id, data_id))
            updated_n_strains = cursor.rowcount
            if not updated_n_strains:
                cursor.execute(
                        "SELECT * FROM "
                        "NStrain WHERE StrainId = "
                        "%s AND DataId = %s" % (strain_id, data_id))
                if not cursor.fetchone():
                    cursor.execute(("INSERT INTO NStrain "
                                    "(StrainId, DataId, count) "
                                    "VALUES (%s, %s, %s)") %
                                   (strain_id, data_id, count))
                    updated_n_strains = cursor.rowcount
    return (updated_published_data,
            updated_se_data, updated_n_strains)


def delete_sample_data(conn: Any,
                       trait_name: str,
                       strain_name: str,
                       phenotype_id: int):
    """Given the right parameters, delete sample-data from the relevant
    table."""
    strain_id, data_id = "", ""

    deleted_published_data: int = 0
    deleted_se_data: int = 0
    deleted_n_strains: int = 0

    with conn.cursor() as cursor:
        # Delete the PublishData table
        try:
            cursor.execute(
                ("SELECT Strain.Id, PublishData.Id FROM "
                 "(PublishData, Strain, PublishXRef, PublishFreeze) "
                 "LEFT JOIN PublishSE ON "
                 "(PublishSE.DataId = PublishData.Id AND "
                 "PublishSE.StrainId = PublishData.StrainId) "
                 "LEFT JOIN NStrain ON "
                 "(NStrain.DataId = PublishData.Id AND "
                 "NStrain.StrainId = PublishData.StrainId) "
                 "WHERE PublishXRef.InbredSetId = "
                 "PublishFreeze.InbredSetId AND "
                 "PublishData.Id = PublishXRef.DataId AND "
                 "PublishXRef.Id = %s AND "
                 "PublishXRef.PhenotypeId = %s "
                 "AND PublishData.StrainId = Strain.Id "
                 "AND Strain.Name = \"%s\"") % (trait_name,
                                                phenotype_id,
                                                str(strain_name)))

            # Check if it exists if the data was already deleted:
            if _result := cursor.fetchone():
                strain_id, data_id = _result

            # Only run if the strain_id and data_id exist
            if strain_id and data_id:
                cursor.execute(("DELETE FROM PublishData "
                                "WHERE StrainId = %s AND Id = %s")
                               % (strain_id, data_id))
                deleted_published_data = cursor.rowcount

                # Delete the PublishSE table
                cursor.execute(("DELETE FROM PublishSE "
                                "WHERE StrainId = %s AND DataId = %s") %
                               (strain_id, data_id))
                deleted_se_data = cursor.rowcount

                # Delete the NStrain table
                cursor.execute(("DELETE FROM NStrain "
                                "WHERE StrainId = %s AND DataId = %s" %
                                (strain_id, data_id)))
                deleted_n_strains = cursor.rowcount
        except Exception as e:  #pylint: disable=[C0103, W0612]
            conn.rollback()
            raise MySQLdb.Error
        conn.commit()
        cursor.close()
        cursor.close()

    return (deleted_published_data,
            deleted_se_data, deleted_n_strains)


def insert_sample_data(conn: Any,  # pylint: disable=[R0913]
                       trait_name: str,
                       strain_name: str,
                       phenotype_id: int,
                       value: Union[int, float, str],
                       error: Union[int, float, str],
                       count: Union[int, str]):
    """Given the right parameters, insert sample-data to the relevant table.

    """

    inserted_published_data, inserted_se_data, inserted_n_strains = 0, 0, 0
    with conn.cursor() as cursor:
        try:
            cursor.execute("SELECT DataId FROM PublishXRef WHERE Id = %s AND "
                           "PhenotypeId = %s", (trait_name, phenotype_id))
            data_id = cursor.fetchone()

            cursor.execute("SELECT Id FROM Strain WHERE Name = %s",
                           (strain_name,))
            strain_id = cursor.fetchone()

            # Return early if an insert already exists!
            cursor.execute("SELECT Id FROM PublishData where Id = %s "
                           "AND StrainId = %s",
                           (data_id, strain_id))
            if cursor.fetchone():  # This strain already exists
                return (0, 0, 0)

            # Insert the PublishData table
            cursor.execute(("INSERT INTO PublishData (Id, StrainId, value)"
                            "VALUES (%s, %s, %s)"),
                           (data_id, strain_id, value))
            inserted_published_data = cursor.rowcount

            # Insert into the PublishSE table if error is specified
            if error and error != "x":
                cursor.execute(("INSERT INTO PublishSE (StrainId, DataId, "
                                " error) VALUES (%s, %s, %s)") %
                               (strain_id, data_id, error))
            inserted_se_data = cursor.rowcount

            # Insert into the NStrain table
            if count and count != "x":
                cursor.execute(("INSERT INTO NStrain "
                                "(StrainId, DataId, count) "
                                "VALUES (%s, %s, %s)") %
                               (strain_id, data_id, count))
            inserted_n_strains = cursor.rowcount
        except Exception:  # pylint: disable=[C0103, W0612]
            conn.rollback()
            raise MySQLdb.Error
    return (inserted_published_data,
            inserted_se_data, inserted_n_strains)
