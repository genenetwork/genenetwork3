from typing import Any, Dict, Union

def retrieve_probeset_trait_dataset_name(
        threshold: int, name: str, connection: Any):
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
            cursor.fetchone))

def retrieve_publish_trait_dataset_name(threshold: int, name: str, connection: Any):
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
            cursor.fetchone))

def retrieve_geno_trait_dataset_name(threshold: int, name: str, connection: Any):
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
            cursor.fetchone))

def retrieve_temp_trait_dataset_name(threshold: int, name: str, connection: Any):
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
            cursor.fetchone))

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


def retrieve_geno_riset_fields(name, conn):
    """
    Retrieve the RISet, and RISetID values for various Geno trait types.
    """
    query = (
        "SELECT InbredSet.Name, InbredSet.Id "
        "FROM InbredSet, GenoFreeze "
        "WHERE GenoFreeze.InbredSetId = InbredSet.Id "
        "AND GenoFreeze.Name = %(name)s")
    with conn.cursor() as cursor:
        cursor.execute(query, {"name": name})
        return dict(zip(["riset", "risetid"], cursor.fetchone()))
    return {}

def retrieve_publish_riset_fields(name, conn):
    """
    Retrieve the RISet, and RISetID values for various Publish trait types.
    """
    query = (
        "SELECT InbredSet.Name, InbredSet.Id "
        "FROM InbredSet, PublishFreeze "
        "WHERE PublishFreeze.InbredSetId = InbredSet.Id "
        "AND PublishFreeze.Name = %(name)s")
    with conn.cursor() as cursor:
        cursor.execute(query, {"name": name})
        return dict(zip(["riset", "risetid"], cursor.fetchone()))
    return {}

def retrieve_probeset_riset_fields(name, conn):
    """
    Retrieve the RISet, and RISetID values for various ProbeSet trait types.
    """
    query = (
        "SELECT InbredSet.Name, InbredSet.Id "
        "FROM InbredSet, ProbeSetFreeze, ProbeFreeze "
        "WHERE ProbeFreeze.InbredSetId = InbredSet.Id "
        "AND ProbeFreeze.Id = ProbeSetFreeze.ProbeFreezeId "
        "AND ProbeSetFreeze.Name = %(name)s")
    with conn.cursor() as cursor:
        cursor.execute(query, {"name": name})
        return dict(zip(["riset", "risetid"], cursor.fetchone()))
    return {}

def retrieve_temp_riset_fields(name, conn):
    query = (
        "SELECT InbredSet.Name, InbredSet.Id "
        "FROM InbredSet, Temp "
        "WHERE Temp.InbredSetId = InbredSet.Id "
        "AND Temp.Name = %(name)s")
    with conn.cursor() as cursor:
        cursor.execute(query, {"name": name})
        return dict(zip(["riset", "risetid"], cursor.fetchone()))
    return {}

def retrieve_riset_fields(trait_type, trait_name, dataset_info, conn):
    """
    Retrieve the RISet, and RISetID values for various trait types.
    """
    riset_fns_map = {
        "Geno": retrieve_geno_riset_fields,
        "Publish": retrieve_publish_riset_fields,
        "ProbeSet": retrieve_probeset_riset_fields
    }

    if trait_type == "Temp":
        riset_info = retrieve_temp_riset_fields(trait_name, conn)
    else:
        riset_info = riset_fns_map[trait_type](dataset_info["dataset_name"], conn)

    return {
        **dataset_info,
        **riset_info,
        "riset": (
            "BXD" if riset_info.get("riset") == "BXD300"
            else riset_info.get("riset", ""))
    }

def retrieve_temp_trait_dataset():
    return {
        "searchfield": ["name", "description"],
        "disfield": ["name", "description"],
        "type": "Temp",
        "dataset_id": 1,
        "fullname": "Temporary Storage",
        "shortname": "Temp"
    }

def retrieve_geno_trait_dataset():
    return {
        "searchfield": ["name","chr"],
	"disfield": ["name","chr","mb", "source2", "sequence"],
	"type": "Geno"
    }

def retrieve_publish_trait_dataset():
    return {
        "searchfield": [
            "name", "post_publication_description", "abstract", "title",
            "authors"],
        "disfield": [
            "name","pubmed_id", "pre_publication_description",
            "post_publication_description", "original_description", 
	    "pre_publication_abbreviation", "post_publication_abbreviation",
	    "lab_code", "submitter", "owner", "authorized_users",
	    "authors","title","abstract", "journal","volume","pages","month",
	    "year","sequence", "units", "comments"],
        "type": "Publish"
    }

def retrieve_probeset_trait_dataset():
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
        trait_type, threshold, trait["trait_name"], trait["db"]["dataset_name"],
        conn)
    }
    riset = retrieve_riset_fields(
        trait_type, trait["trait_name"], dataset_name_info, conn)
    return {
        "display_name": dataset_name_info["dataset_name"],
        **dataset_name_info,
        **dataset_fns[trait_type](),
        **riset
    }
