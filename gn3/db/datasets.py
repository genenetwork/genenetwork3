"""
This module contains functions relating to specific trait dataset manipulation
"""
import re
from string import Template
from typing import Any, Dict, List, Optional
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
        res = cursor.fetchone()
        if res:
            return dict(zip(
                ["dataset_id", "dataset_name", "dataset_fullname",
                 "dataset_shortname", "dataset_datascale"],
                res))
        return {"dataset_id": None, "dataset_name": name, "dataset_fullname": name}

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

def sparql_query(query: str) -> List[Dict[str, Any]]:
    """Run a SPARQL query and return the bound variables."""
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.queryAndConvert()['results']['bindings']

def dataset_metadata(accession_id: str) -> Optional[Dict[str, Any]]:
    """Return info about dataset with ACCESSION_ID."""
    # Check accession_id to protect against query injection.
    # TODO: This function doesn't yet return the names of the actual dataset files.
    pattern = re.compile(r'GN\d+', re.ASCII)
    if not pattern.fullmatch(accession_id):
        return None
    # KLUDGE: We split the SPARQL query because virtuoso is very slow on a
    # single large query.
    queries = ["""
PREFIX gn: <http://genenetwork.org/>
SELECT ?name ?dataset_group ?status ?title ?geo_series
WHERE {
  ?dataset gn:accessionId "$accession_id" ;
           rdf:type gn:dataset ;
           gn:name ?name .
  OPTIONAL { ?dataset gn:datasetGroup ?dataset_group } .
  # FIXME: gn:datasetStatus should not be optional. But, some records don't
  # have it.
  OPTIONAL { ?dataset gn:datasetStatus ?status } .
  OPTIONAL { ?dataset gn:title ?title } .
  OPTIONAL { ?dataset gn:geoSeries ?geo_series } .
}
""",
               """
PREFIX gn: <http://genenetwork.org/>
SELECT ?platform_name ?normalization_name ?species_name ?inbred_set_name ?tissue_name
WHERE {
  ?dataset gn:accessionId "$accession_id" ;
           rdf:type gn:dataset ;
           gn:normalization / gn:name ?normalization_name ;
           gn:datasetOfSpecies / gn:menuName ?species_name ;
           gn:datasetOfInbredSet / gn:name ?inbred_set_name .
  OPTIONAL { ?dataset gn:datasetOfTissue / gn:name ?tissue_name } .
  OPTIONAL { ?dataset gn:datasetOfPlatform / gn:name ?platform_name } .
}
""",
               """
PREFIX gn: <http://genenetwork.org/>
SELECT ?specifics ?summary ?about_cases ?about_tissue ?about_platform
       ?about_data_processing ?notes ?experiment_design ?contributors
       ?citation ?acknowledgment
WHERE {
  ?dataset gn:accessionId "$accession_id" ;
           rdf:type gn:dataset .
  OPTIONAL { ?dataset gn:specifics ?specifics . }
  OPTIONAL { ?dataset gn:summary ?summary . }
  OPTIONAL { ?dataset gn:aboutCases ?about_cases . }
  OPTIONAL { ?dataset gn:aboutTissue ?about_tissue . }
  OPTIONAL { ?dataset gn:aboutPlatform ?about_platform . }
  OPTIONAL { ?dataset gn:aboutDataProcessing ?about_data_processing . }
  OPTIONAL { ?dataset gn:notes ?notes . }
  OPTIONAL { ?dataset gn:experimentDesign ?experiment_design . }
  OPTIONAL { ?dataset gn:contributors ?contributors . }
  OPTIONAL { ?dataset gn:citation ?citation . }
  OPTIONAL { ?dataset gn:acknowledgment ?acknowledgment . }
}
"""]
    result = {'accession_id': accession_id,
              'investigator': {}}
    query_result = {}
    for query in queries:
        if sparql_result := sparql_query(Template(query).substitute(accession_id=accession_id)):
            query_result.update(sparql_result[0])
        else:
            return None
    for key, value in query_result.items():
        result[key] = value['value']
    investigator_query_result = sparql_query(Template("""
PREFIX gn: <http://genenetwork.org/>
SELECT ?name ?address ?city ?state ?zip ?phone ?email ?country ?homepage
WHERE {
  ?dataset gn:accessionId "$accession_id" ;
           rdf:type gn:dataset ;
           gn:datasetOfInvestigator ?investigator .
  OPTIONAL { ?investigator foaf:name ?name . }
  OPTIONAL { ?investigator gn:address ?address . }
  OPTIONAL { ?investigator gn:city ?city . }
  OPTIONAL { ?investigator gn:state ?state . }
  OPTIONAL { ?investigator gn:zipCode ?zip . }
  OPTIONAL { ?investigator foaf:phone ?phone . }
  OPTIONAL { ?investigator foaf:mbox ?email . }
  OPTIONAL { ?investigator gn:country ?country . }
  OPTIONAL { ?investigator foaf:homepage ?homepage . }
}
""").substitute(accession_id=accession_id))[0]
    for key, value in investigator_query_result.items():
        result['investigator'][key] = value['value']
    return result
