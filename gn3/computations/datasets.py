"""module contains the code all related to datasets"""
import json
from math import ceil
from collections import defaultdict

from typing import Optional
from typing import List

from dataclasses import dataclass
from MySQLdb import escape_string  # type: ignore

import requests
from gn3.settings import GN2_BASE_URL


def retrieve_trait_sample_data(dataset,
                               trait_name: str,
                               database,
                               group_species_id=None) -> List:
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

        results = fetch_from_db_sample_data(formatted_query, database)

    return results


def fetch_from_db_sample_data(formatted_query: str, database_instance) -> List:
    """this is the function that does the actual fetching of\
    results from the database"""
    try:
        cursor = database_instance.cursor()
        cursor.execute(formatted_query)
        results = cursor.fetchall()

    except Exception as error:
        raise error

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
                        (ProbeSetData, ProbeSetFreeze,
                         Strain, ProbeSet, ProbeSetXRef)
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


@dataclass
class Dataset:
    """class for creating datasets"""
    name: Optional[str] = None
    dataset_type: Optional[str] = None
    dataset_id: int = -1


def create_mrna_tissue_dataset(dataset_name, dataset_type):
    """an mrna assay is a quantitative assessment(assay) associated\
    with an mrna trait.This used to be called probeset,but that term\
    only referes specifically to the afffymetrix platform and is\
    far too speficified"""

    return Dataset(name=dataset_name, dataset_type=dataset_type)


def dataset_type_getter(dataset_name, redis_instance=None) -> Optional[str]:
    """given the dataset name fetch the type\
    of the dataset this in turn  enables fetching\
    the creation of the correct object could utilize\
    redis for the case"""

    results = redis_instance.get(dataset_name, None)

    if results:
        return results

    return fetch_dataset_type_from_gn2_api(dataset_name)


def fetch_dataset_type_from_gn2_api(dataset_name):
    """this function is only called when the\
    the redis is empty and does have the specificied\
    dataset_type"""
    # should only run once

    dataset_structure = {}

    map_dataset_to_new_type = {
        "Phenotypes": "Publish",
        "Genotypes": "Geno",
        "MrnaTypes": "ProbeSet"
    }

    data = json.loads(requests.get(
        GN2_BASE_URL + "/api/v_pre1/gen_dropdown", timeout=5).content)
    _name = dataset_name
    for species in data['datasets']:
        for group in data['datasets'][species]:
            for dataset_type in data['datasets'][species][group]:
                for dataset in data['datasets'][species][group][dataset_type]:
                    # assumes  the first is dataset_short_name
                    short_dataset_name = next(
                        item for item in dataset if item != "None" and item is not None)

                    dataset_structure[short_dataset_name] = map_dataset_to_new_type.get(
                        dataset_type, "MrnaTypes")
    return dataset_structure


def dataset_creator_store(dataset_type):
    """function contains key value pairs for\
    the function need to be called to create\
    each dataset_type"""

    dataset_obj = {
        "ProbeSet": create_mrna_tissue_dataset
    }

    return dataset_obj[dataset_type]


def create_dataset(dataset_type=None, dataset_name: str = None):
    """function for creating new dataset  temp not implemented"""
    if dataset_type is None:
        dataset_type = dataset_type_getter(dataset_name)

    dataset_creator = dataset_creator_store(dataset_type)
    results = dataset_creator(
        dataset_name=dataset_name, dataset_type=dataset_type)
    return results


def fetch_dataset_sample_id(samplelist: List, database, species: str) -> dict:
    """fetch the strain ids from the db only if\
    it is in the samplelist"""
    # xtodo create an in clause for samplelist

    strain_query = """
        SELECT Strain.Name, Strain.Id FROM Strain, Species
        WHERE Strain.Name IN {}
        and Strain.SpeciesId=Species.Id
        and Species.name = '{}'
        """

    database_cursor = database.cursor()
    database_cursor.execute(strain_query.format(samplelist, species))

    results = database_cursor.fetchall()

    return dict(results)


def divide_into_chunks(the_list, number_chunks):
    """Divides a list into approximately number_chunks
    >>> divide_into_chunks([1, 2, 7, 3, 22, 8, 5, 22, 333], 3)
    [[1, 2, 7], [3, 22, 8], [5, 22, 333]]"""

    length = len(the_list)
    if length == 0:
        return [[]]

    if length <= number_chunks:
        number_chunks = length
    chunk_size = int(ceil(length/number_chunks))
    chunks = []

    for counter in range(0, length, chunk_size):
        chunks.append(the_list[counter:counter+chunk_size])
    return chunks


def escape(string_):
    """function escape sql value"""
    return escape_string(string_).decode('utf8')


def mescape(*items) -> List:
    """multiple escape for query values"""

    return [escape_string(str(item)).decode('utf8') for item in items]


def get_traits_data(sample_ids, database_instance, dataset_name, dataset_type):
    """function to fetch trait data"""
    # MySQL limits the number of tables that can be used in a join to 61,
    # so we break the sample ids into smaller chunks
    # Postgres doesn't have that limit, so we can get rid of this after we transition

    _trait_data = defaultdict(list)
    chunk_size = 61
    number_chunks = int(ceil(len(sample_ids) / chunk_size))
    for sample_ids_step in divide_into_chunks(sample_ids, number_chunks):
        if dataset_type == "Publish":
            full_dataset_type = "Phenotype"
        else:
            full_dataset_type = dataset_type
        temp = ['T%s.value' % item for item in sample_ids_step]

        if dataset_type == "Publish":
            query = "SELECT {}XRef.Id,".format(escape(dataset_type))

        else:
            query = "SELECT {}.Name,".format(escape(full_dataset_type))

        query += ', '.join(temp)
        query += ' FROM ({}, {}XRef, {}Freeze) '.format(*mescape(full_dataset_type,
                                                                 dataset_type,
                                                                 dataset_type))
        for item in sample_ids_step:

            query += """
                    left join {}Data as T{} on T{}.Id = {}XRef.DataId
                    and T{}.StrainId={}\n
                    """.format(*mescape(dataset_type, item,
                                        item, dataset_type, item, item))

        if dataset_type == "Publish":
            query += """
                        WHERE {}XRef.{}FreezeId = {}Freeze.Id
                        and {}Freeze.Name = '{}'
                        and {}.Id = {}XRef.{}Id
                        order by {}.Id
                        """.format(*mescape(dataset_type, dataset_type,
                                            dataset_type, dataset_type,
                                            dataset_name, full_dataset_type,
                                            dataset_type, dataset_type,
                                            full_dataset_type))

        else:
            query += """
                        WHERE {}XRef.{}FreezeId = {}Freeze.Id
                        and {}Freeze.Name = '{}'
                        and {}.Id = {}XRef.{}Id
                        order by {}.Id
                        """.format(*mescape(dataset_type, dataset_type,
                                            dataset_type, dataset_type,
                                            dataset_name, dataset_type,
                                            dataset_type, dataset_type,
                                            full_dataset_type))

        # print(query)

        _results = fetch_from_db_sample_data(query, database_instance)

        return []


def get_probeset_trait_data(strain_ids: List, conn, dataset_name) -> dict:
    """function for getting trait data\
    for probeset data type similar to\
    get trait data only difference is that\
    it uses sub queries"""

    trait_data: dict = {}

    trait_id_name = {}

    traits_query = """
    SELECT ProbeSetXRef.DataId,ProbeSet.Name FROM (ProbeSet, ProbeSetXRef, ProbeSetFreeze)
                    WHERE ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id
                    and ProbeSetFreeze.Name = '{}'
                    and ProbeSet.Id = ProbeSetXRef.ProbeSetId
                    order by ProbeSet.Id
    """.format(dataset_name)

    query = """
    SELECT * from ProbeSetData
    where StrainID in ({})
    and id in (SELECT ProbeSetXRef.DataId FROM (ProbeSet, ProbeSetXRef, ProbeSetFreeze)
                WHERE ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id
                and ProbeSetFreeze.Name = '{}'
                and ProbeSet.Id = ProbeSetXRef.ProbeSetId
                order by ProbeSet.Id)
    """.format(",".join(str(strain_id) for strain_id in strain_ids), dataset_name)

    with conn:
        cursor = conn.cursor()
        cursor.execute(query)
        _results = cursor.fetchall()
        cursor.execute(traits_query)
        trait_id_name = dict(cursor.fetchall())

    for trait_id, _strain_id, strain_value in _results:
        trait_name = trait_id_name[trait_id]
        if trait_data.get(trait_name):
            trait_data[trait_name].append(strain_value)
        else:
            trait_data[trait_name] = []

            trait_data[trait_name].append(strain_value)

    return trait_data
