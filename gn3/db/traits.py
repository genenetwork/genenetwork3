"""This class contains functions relating to trait data manipulation"""
from typing import Any


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
