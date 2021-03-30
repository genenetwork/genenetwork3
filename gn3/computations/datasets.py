"""module contains the code all related to datasets"""
from unittest import mock

from typing import Optional
from typing import List


def retrieve_trait_sample_data(dataset_id, dataset_type: str, trait_name: str) -> List:
    """given the dataset id and trait_name fetch the\
    sample_name,value from the dataset"""

    # should pass the db as arg all  do a setup

    _func_args = (dataset_id, dataset_type, trait_name)
    dataset_query = get_query_for_dataset_sample(dataset_type)

    if dataset_query:
        if dataset_type == "Publish":
            formatted_query = dataset_query % (trait_name, dataset_id)
            results = fetch_from_db_sample_data(formatted_query, mock.Mock())
            return results

        return []

    return []


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

    dataset_query["Publish"] = pheno_query

    return dataset_query.get(dataset_type)
