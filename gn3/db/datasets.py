"""
This module contains functions relating to specific trait dataset manipulation
"""
import re
from string import Template
from typing import Any, Dict, Optional
from SPARQLWrapper import JSON, SPARQLWrapper
from gn3.settings import SPARQL_ENDPOINT

def retrieve_probeset_trait_dataset_name(
        threshold: int, name: str, connection: Any):
    """
    Get the ID, DataScale and various name formats for a `ProbeSet` trait.
    """
    query = (
        "SELECT Id, Name, FullName, ShortName, DataScale "
        "FROM ProbeSetFreeze "
        "WHERE "
        "public > %(threshold)s "
        "AND "
        "(Name = %(name)s OR FullName = %(name)s OR ShortName = %(name)s)")
    with connection.cursor() as cursor:
        cursor.execute(
            query,
            {
                "threshold": threshold,
                "name": name
            })
        return dict(zip(
            ["dataset_id", "dataset_name", "dataset_fullname",
             "dataset_shortname", "dataset_datascale"],
            cursor.fetchone()))

def retrieve_publish_trait_dataset_name(
        threshold: int, name: str, connection: Any):
    """
    Get the ID, DataScale and various name formats for a `Publish` trait.
    """
    query = (
        "SELECT Id, Name, FullName, ShortName "
        "FROM PublishFreeze "
        "WHERE "
        "public > %(threshold)s "
        "AND "
        "(Name = %(name)s OR FullName = %(name)s OR ShortName = %(name)s)")
    with connection.cursor() as cursor:
        cursor.execute(
            query,
            {
                "threshold": threshold,
                "name": name
            })
        return dict(zip(
            ["dataset_id", "dataset_name", "dataset_fullname",
             "dataset_shortname"],
            cursor.fetchone()))

def retrieve_geno_trait_dataset_name(
        threshold: int, name: str, connection: Any):
    """
    Get the ID, DataScale and various name formats for a `Geno` trait.
    """
    query = (
        "SELECT Id, Name, FullName, ShortName "
        "FROM GenoFreeze "
        "WHERE "
        "public > %(threshold)s "
        "AND "
        "(Name = %(name)s OR FullName = %(name)s OR ShortName = %(name)s)")
    with connection.cursor() as cursor:
        cursor.execute(
            query,
            {
                "threshold": threshold,
                "name": name
            })
        return dict(zip(
            ["dataset_id", "dataset_name", "dataset_fullname",
             "dataset_shortname"],
            cursor.fetchone()))

def retrieve_temp_trait_dataset_name(
        threshold: int, name: str, connection: Any):
    """
    Get the ID, DataScale and various name formats for a `Temp` trait.
    """
    query = (
        "SELECT Id, Name, FullName, ShortName "
        "FROM TempFreeze "
        "WHERE "
        "public > %(threshold)s "
        "AND "
        "(Name = %(name)s OR FullName = %(name)s OR ShortName = %(name)s)")
    with connection.cursor() as cursor:
        cursor.execute(
            query,
            {
                "threshold": threshold,
                "name": name
            })
        return dict(zip(
            ["dataset_id", "dataset_name", "dataset_fullname",
             "dataset_shortname"],
            cursor.fetchone()))

def retrieve_dataset_name(
        trait_type: str, threshold: int, trait_name: str, dataset_name: str,
        conn: Any):
    """
    Retrieve the name of a trait given the trait's name

    This is extracted from the `webqtlDataset.retrieveName` function as is
    implemented at
    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/base/webqtlDataset.py#L140-L169
    """
    fn_map = {
        "ProbeSet": retrieve_probeset_trait_dataset_name,
        "Publish": retrieve_publish_trait_dataset_name,
        "Geno": retrieve_geno_trait_dataset_name,
        "Temp": retrieve_temp_trait_dataset_name}
    if trait_type == "Temp":
        return retrieve_temp_trait_dataset_name(threshold, trait_name, conn)
    return fn_map[trait_type](threshold, dataset_name, conn)


def retrieve_geno_group_fields(name, conn):
    """
    Retrieve the Group, and GroupID values for various Geno trait types.
    """
    query = (
        "SELECT InbredSet.Name, InbredSet.Id "
        "FROM InbredSet, GenoFreeze "
        "WHERE GenoFreeze.InbredSetId = InbredSet.Id "
        "AND GenoFreeze.Name = %(name)s")
    with conn.cursor() as cursor:
        cursor.execute(query, {"name": name})
        return dict(zip(["group", "groupid"], cursor.fetchone()))
    return {}

def retrieve_publish_group_fields(name, conn):
    """
    Retrieve the Group, and GroupID values for various Publish trait types.
    """
    query = (
        "SELECT InbredSet.Name, InbredSet.Id "
        "FROM InbredSet, PublishFreeze "
        "WHERE PublishFreeze.InbredSetId = InbredSet.Id "
        "AND PublishFreeze.Name = %(name)s")
    with conn.cursor() as cursor:
        cursor.execute(query, {"name": name})
        return dict(zip(["group", "groupid"], cursor.fetchone()))
    return {}

def retrieve_probeset_group_fields(name, conn):
    """
    Retrieve the Group, and GroupID values for various ProbeSet trait types.
    """
    query = (
        "SELECT InbredSet.Name, InbredSet.Id "
        "FROM InbredSet, ProbeSetFreeze, ProbeFreeze "
        "WHERE ProbeFreeze.InbredSetId = InbredSet.Id "
        "AND ProbeFreeze.Id = ProbeSetFreeze.ProbeFreezeId "
        "AND ProbeSetFreeze.Name = %(name)s")
    with conn.cursor() as cursor:
        cursor.execute(query, {"name": name})
        return dict(zip(["group", "groupid"], cursor.fetchone()))
    return {}

def retrieve_temp_group_fields(name, conn):
    """
    Retrieve the Group, and GroupID values for `Temp` trait types.
    """
    query = (
        "SELECT InbredSet.Name, InbredSet.Id "
        "FROM InbredSet, Temp "
        "WHERE Temp.InbredSetId = InbredSet.Id "
        "AND Temp.Name = %(name)s")
    with conn.cursor() as cursor:
        cursor.execute(query, {"name": name})
        return dict(zip(["group", "groupid"], cursor.fetchone()))
    return {}

def retrieve_group_fields(trait_type, trait_name, dataset_info, conn):
    """
    Retrieve the Group, and GroupID values for various trait types.
    """
    group_fns_map = {
        "Geno": retrieve_geno_group_fields,
        "Publish": retrieve_publish_group_fields,
        "ProbeSet": retrieve_probeset_group_fields
    }

    if trait_type == "Temp":
        group_info = retrieve_temp_group_fields(trait_name, conn)
    else:
        group_info = group_fns_map[trait_type](dataset_info["dataset_name"], conn)

    return {
        **dataset_info,
        **group_info,
        "group": (
            "BXD" if group_info.get("group") == "BXD300"
            else group_info.get("group", ""))
    }

def retrieve_temp_trait_dataset():
    """
    Retrieve the dataset that relates to `Temp` traits
    """
    # pylint: disable=[C0330]
    return {
        "searchfield": ["name", "description"],
        "disfield": ["name", "description"],
        "type": "Temp",
        "dataset_id": 1,
        "fullname": "Temporary Storage",
        "shortname": "Temp"
    }

def retrieve_geno_trait_dataset():
    """
    Retrieve the dataset that relates to `Geno` traits
    """
    # pylint: disable=[C0330]
    return {
        "searchfield": ["name", "chr"],
	"disfield": ["name", "chr", "mb", "source2", "sequence"],
	"type": "Geno"
    }

def retrieve_publish_trait_dataset():
    """
    Retrieve the dataset that relates to `Publish` traits
    """
    # pylint: disable=[C0330]
    return {
        "searchfield": [
            "name", "post_publication_description", "abstract", "title",
            "authors"],
        "disfield": [
            "name", "pubmed_id", "pre_publication_description",
            "post_publication_description", "original_description",
	    "pre_publication_abbreviation", "post_publication_abbreviation",
	    "lab_code", "submitter", "owner", "authorized_users",
	    "authors", "title", "abstract", "journal", "volume", "pages",
            "month", "year", "sequence", "units", "comments"],
        "type": "Publish"
    }

def retrieve_probeset_trait_dataset():
    """
    Retrieve the dataset that relates to `ProbeSet` traits
    """
    # pylint: disable=[C0330]
    return {
        "searchfield": [
            "name", "description", "probe_target_description", "symbol",
            "alias", "genbankid", "unigeneid", "omim", "refseq_transcriptid",
            "probe_set_specificity", "probe_set_blat_score"],
	"disfield": [
            "name", "symbol", "description", "probe_target_description", "chr",
            "mb", "alias", "geneid", "genbankid", "unigeneid", "omim",
            "refseq_transcriptid", "blatseq", "targetseq", "chipid", "comments",
            "strand_probe", "strand_gene", "probe_set_target_region",
            "proteinid", "probe_set_specificity", "probe_set_blat_score",
            "probe_set_blat_mb_start", "probe_set_blat_mb_end",
            "probe_set_strand", "probe_set_note_by_rw", "flag"],
	"type": "ProbeSet"
    }

def retrieve_trait_dataset(trait_type, trait, threshold, conn):
    """
    Retrieve the dataset that relates to a specific trait.
    """
    dataset_fns = {
        "Temp": retrieve_temp_trait_dataset,
        "Geno": retrieve_geno_trait_dataset,
        "Publish": retrieve_publish_trait_dataset,
        "ProbeSet": retrieve_probeset_trait_dataset
    }
    dataset_name_info = {
        "dataset_id": None,
        "dataset_name": trait["db"]["dataset_name"],
        **retrieve_dataset_name(
            trait_type, threshold, trait["trait_name"],
            trait["db"]["dataset_name"], conn)
    }
    group = retrieve_group_fields(
        trait_type, trait["trait_name"], dataset_name_info, conn)
    return {
        "display_name": dataset_name_info["dataset_name"],
        **dataset_name_info,
        **dataset_fns[trait_type](),
        **group
    }

def dataset_metadata(accession_id: str) -> Optional[Dict[str, Any]]:
    """Return info about dataset with ACCESSION_ID."""
    # Check accession_id to protect against query injection.
    pattern = re.compile(r'GN\d+', re.ASCII)
    if not pattern.fullmatch(accession_id):
        return None
    query = Template("""
PREFIX gn: <https://genenetwork.org/>
SELECT ?name ?geo_series ?title ?status ?platform_name ?normalization_name
       ?species_name ?inbred_set_name ?tissue_name
       ?investigator_name ?investigator_address ?investigator_city
       ?investigator_state ?investigator_zip ?investigator_phone
       ?investigator_email ?investigator_country ?investigator_homepage
       ?specifics ?summary ?about_cases ?about_tissue ?about_platform
       ?about_data_processing ?notes ?experiment_design ?contributors
       ?citation ?acknowledgment
WHERE {
  ?dataset rdf:type gn:dataset .
  ?dataset gn:name ?name .
  ?dataset gn:geoSeries ?geo_series .
  ?dataset gn:title ?title .
  ?dataset gn:datasetStatus ?status .

  ?dataset gn:datasetOfPlatform ?platform .
  ?platform gn:name ?platform_name .

  ?dataset gn:normalization ?normalization .
  ?normalization gn:name ?normalization_name .

  ?dataset gn:datasetOfSpecies ?species .
  ?species gn:menuName ?species_name .

  ?dataset gn:datasetOfInbredSet ?inbredSet .
  ?inbredSet gn:name ?inbred_set_name .

  ?dataset gn:datasetOfTissue ?tissue .
  ?tissue gn:name ?tissue_name .

  OPTIONAL { ?dataset gn:datasetOfInvestigator ?investigator . }
  OPTIONAL { ?investigator foaf:name ?investigator_name . }
  OPTIONAL { ?investigator gn:address ?investigator_address . }
  OPTIONAL { ?investigator gn:city ?investigator_city . }
  OPTIONAL { ?investigator gn:state ?investigator_state . }
  OPTIONAL { ?investigator gn:zipCode ?investigator_zip . }
  OPTIONAL { ?investigator foaf:phone ?investigator_phone . }
  OPTIONAL { ?investigator foaf:mbox ?investigator_email . }
  OPTIONAL { ?investigator gn:country ?investigator_country . }
  OPTIONAL { ?investigator foaf:homepage ?investigator_homepage . }

  OPTIONAL { ?dataset gn:specifics ?specifics . }
  OPTIONAL { ?dataset gn:summary ?summary . }
  OPTIONAL { ?dataset gn:aboutCases ?about_cases . }
  OPTIONAL { ?dataset gn:aboutTissue ?about_tissue . }
  OPTIONAL { ?dataset gn:aboutPlatform ?about_platform . }
  OPTIONAL { ?dataset gn:aboutDataProcessing ?about_data_processing . }
  OPTIONAL { ?dataset gn:notes ?notes . }
  OPTIONAL { ?dataset gn:experimentDesign ?experiment_design . }
  OPTIONAL { ?dataset gn:contributors ?contributors . }
  OPTIONAL { ?dataset gn:accessionId '$accession_id' . }
  OPTIONAL { ?dataset gn:citation ?citation . }
  OPTIONAL { ?dataset gn:acknowledgment ?acknowledgment . }
}
""")
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    sparql.setQuery(query.substitute(accession_id=accession_id))
    sparql.setReturnFormat(JSON)
    query_results = sparql.queryAndConvert()
    query_result = query_results['results']['bindings'][0]
    # Build result dictionary, putting investigator metadata into a nested
    # dictionary.
    result = {}
    for key, value in query_result.items():
        if key.startswith('investigator_'):
            if 'investigator' not in result:
                result['investigator'] = {}
            result['investigator'][key[len('investigator_'):]] = value['value']
        else:
            result[key] = value['value']
    return result if result else None
