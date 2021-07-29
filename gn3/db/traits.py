"""This class contains functions relating to trait data manipulation"""
from typing import Any, Union


def get_trait_csv_sample_data(conn: Any,
                              trait_name: int, phenotype_id: int):
    """Fetch a trait and return it as a csv string"""
    sql = ("SELECT  Strain.Id, PublishData.Id, Strain.Name, "
           "PublishData.value, "
           "PublishSE.error, NStrain.count FROM "
           "(PublishData, Strain, PublishXRef, PublishFreeze) "
           "LEFT JOIN PublishSE ON "
           "(PublishSE.DataId = PublishData.Id AND "
           "PublishSE.StrainId = PublishData.StrainId) "
           "LEFT JOIN NStrain ON (NStrain.DataId = PublishData.Id AND "
           "NStrain.StrainId = PublishData.StrainId) WHERE "
           "PublishXRef.InbredSetId = PublishFreeze.InbredSetId AND "
           "PublishData.Id = PublishXRef.DataId AND "
           "PublishXRef.Id = %s AND PublishXRef.PhenotypeId = %s "
           "AND PublishData.StrainId = Strain.Id Order BY Strain.Name")
    csv_data = ["Strain Id,Strain Name,Value,SE,Count"]
    publishdata_id = ""
    with conn.cursor() as cursor:
        cursor.execute(sql, (trait_name, phenotype_id,))
        for record in cursor.fetchall():
            (strain_id, publishdata_id,
             strain_name, value, error, count) = record
            csv_data.append(
                ",".join([str(val) if val else "x"
                          for val in (strain_id, strain_name,
                                      value, error, count)]))
    return f"# Publish Data Id: {publishdata_id}\n\n" + "\n".join(csv_data)


def update_sample_data(conn: Any,
                       strain_name: str,
                       strain_id: int,
                       publish_data_id: int,
                       value: Union[int, float, str],
                       error: Union[int, float, str],
                       count: Union[int, str]):
    """Given the right parameters, update sample-data from the relevant
    table."""
    STRAIN_ID_SQL: str = "UPDATE Strain SET Name = %s WHERE Id = %s"
    PUBLISH_DATA_SQL: str = ("UPDATE PublishData SET value = %s "
                             "WHERE StrainId = %s AND Id = %s")
    PUBLISH_SE_SQL: str = ("UPDATE PublishSE SET error = %s "
                           "WHERE StrainId = %s AND DataId = %s")
    N_STRAIN_SQL: str = ("UPDATE NStrain SET count = %s "
                         "WHERE StrainId = %s AND DataId = %s")

    updated_strains: int = 0
    updated_published_data: int = 0
    updated_se_data: int = 0
    updated_n_strains: int = 0

    with conn.cursor() as cursor:
        # Update the Strains table
        cursor.execute(STRAIN_ID_SQL, (strain_name, strain_id))
        updated_strains: int = cursor.rowcount
        # Update the PublishData table
        cursor.execute(PUBLISH_DATA_SQL,
                       (None if value == "x" else value,
                        strain_id, publish_data_id))
        updated_published_data: int = cursor.rowcount
        # Update the PublishSE table
        cursor.execute(PUBLISH_SE_SQL,
                       (None if error == "x" else error,
                        strain_id, publish_data_id))
        updated_se_data: int = cursor.rowcount
        # Update the NStrain table
        cursor.execute(N_STRAIN_SQL,
                       (None if count == "x" else count,
                        strain_id, publish_data_id))
        updated_n_strains: int = cursor.rowcount
    return (updated_strains, updated_published_data,
            updated_se_data, updated_n_strains)
