"""module contains the code all related to datasets"""
from unittest import mock

from typing import Optional
from typing import List


def retrieve_trait_sample_data(dataset,
                               trait_name: str,
                               group_species_id=None,) -> List:
    """given the dataset id and trait_name fetch the\
    sample_name,value from the dataset"""

    # should pass the db as arg all  do a setup

    (dataset_name, dataset_id, dataset_type) = (dataset.get("name"), dataset.get(
        "id"), dataset.get("type"))

    dataset_query = get_query_for_dataset_sample(dataset_type)
    results = []
    sample_query_values = {
        "Publish": (trait_name, dataset_id),
        "Geno": (group_species_id, trait_name, dataset_name),
        "ProbeSet": (trait_name, dataset_name)
    }

    if dataset_query:
        formatted_query = dataset_query % sample_query_values[dataset_type]
        results = fetch_from_db_sample_data(formatted_query, mock.Mock())

    return results


def fetch_from_db_sample_data(formatted_query: str, database_instance) -> List:
    """this is the function that does the actual fetching of\
    results from the database"""
    cursor = database_instance.cursor()
    cursor.execute(formatted_query)
    results = cursor.fetchall()

    cursor.close()

    return results


def get_query_for_dataset_sample(dataset_type) -> Optional[str]:
    """this functions contains querys for\
    getting sample data from the db depending in
    dataset"""
    dataset_query = {}

    pheno_query = """
                SELECT
                        Strain.Name, PublishData.value, PublishSE.error,NStrain.count, Strain.Name2
                FROM
                        (PublishData, Strain, PublishXRef, PublishFreeze)
                left join PublishSE on
                        (PublishSE.DataId = PublishData.Id AND PublishSE.StrainId = PublishData.StrainId)
                left join NStrain on
                        (NStrain.DataId = PublishData.Id AND
                        NStrain.StrainId = PublishData.StrainId)
                WHERE
                        PublishXRef.InbredSetId = PublishFreeze.InbredSetId AND
                        PublishData.Id = PublishXRef.DataId AND PublishXRef.Id = %s AND
                        PublishFreeze.Id = %s AND PublishData.StrainId = Strain.Id
                Order BY
                        Strain.Name
                """
    geno_query = """
                SELECT
                        Strain.Name, GenoData.value, GenoSE.error, "N/A", Strain.Name2
                FROM
                        (GenoData, GenoFreeze, Strain, Geno, GenoXRef)
                left join GenoSE on
                        (GenoSE.DataId = GenoData.Id AND GenoSE.StrainId = GenoData.StrainId)
                WHERE
                        Geno.SpeciesId = %s AND Geno.Name = %s AND GenoXRef.GenoId = Geno.Id AND
                        GenoXRef.GenoFreezeId = GenoFreeze.Id AND
                        GenoFreeze.Name = %s AND
                        GenoXRef.DataId = GenoData.Id AND
                        GenoData.StrainId = Strain.Id
                Order BY
                        Strain.Name
                """

    probeset_query = """
                SELECT
                        Strain.Name, ProbeSetData.value, ProbeSetSE.error, NStrain.count, Strain.Name2
                FROM
                        (ProbeSetData, ProbeSetFreeze, Strain, ProbeSet, ProbeSetXRef)
                left join ProbeSetSE on
                        (ProbeSetSE.DataId = ProbeSetData.Id AND ProbeSetSE.StrainId = ProbeSetData.StrainId)
                left join NStrain on
                        (NStrain.DataId = ProbeSetData.Id AND
                        NStrain.StrainId = ProbeSetData.StrainId)
                WHERE
                        ProbeSet.Name = '%s' AND ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
                        ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND
                        ProbeSetFreeze.Name = '%s' AND
                        ProbeSetXRef.DataId = ProbeSetData.Id AND
                        ProbeSetData.StrainId = Strain.Id
                Order BY
                        Strain.Name
                """

    dataset_query["Publish"] = pheno_query
    dataset_query["Geno"] = geno_query
    dataset_query["ProbeSet"] = probeset_query

    return dataset_query.get(dataset_type)
