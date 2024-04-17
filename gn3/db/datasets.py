"""
This module contains functions relating to specific trait dataset manipulation
"""
import json

from typing import Any
from pathlib import Path

from flask import current_app as app

def retrieve_sample_list(group: str, inc_par: bool = True, inc_f1: bool = True):
    """
    Get the sample list for a group (a category that datasets belong to)

    Currently it is fetched from the .geno files, since that's the only place
    the "official" sample list is stored
    """

    samplelist = []
    if inc_par or inc_f1:
        par_f1_path = Path(
            app.config.get(
                "GENENETWORK_FILES",
                "/home/gn2/production/genotype_files/"
            ), 'parents_and_f1s.json'
        )
        if par_f1_path.is_file():
            with open(par_f1_path, encoding="utf-8") as par_f1_file:
                par_f1s = json.load(par_f1_file).get(group, {})
                if inc_par and par_f1s:
                    samplelist += [par_f1s['paternal']['strain'], par_f1s['maternal']['strain']]
                if inc_f1 and par_f1s:
                    samplelist += [f1['strain'] for f1 in par_f1s['f1s']]

    genofile_path = Path(
        app.config.get(
            "GENENETWORK_FILES",
            "/home/gn2/production/genotype_files/"
        ), f'genotype/{group}.geno'
    )
    if genofile_path.is_file():
        with open(genofile_path, encoding="utf-8") as genofile:
            line = ""
            for line in genofile:
                line = line.strip()
                if not line:
                    continue
                if line.startswith(("#", "@")):
                    continue
                break

            headers = line.split("\t")

            if headers[3] == "Mb":
                samplelist += headers[4:]
            else:
                samplelist += headers[3:]
    return samplelist

def retrieve_mrna_group_name(connection: Any, probeset_id: int, dataset_name: str):
    """
    Given the trait id (ProbeSet.Id in the database), retrieve the name
    of the group the dataset belongs to.
    """
    query = (
        "SELECT iset.Name "
        "FROM ProbeSet ps LEFT JOIN ProbeSetXRef psx ON psx.ProbeSetId = ps.Id "
        "LEFT JOIN ProbeSetFreeze psf ON psx.ProbeSetFreezeId = psf.Id "
        "LEFT JOIN ProbeFreeze pf ON psf.ProbeFreezeId = pf.Id "
        "LEFT JOIN InbredSet iset ON pf.InbredSetId = iset.Id "
        "WHERE ps.Id = %(probeset_id)s AND psf.Name=%(dataset_name)s")
    with connection.cursor() as cursor:
        cursor.execute(query, {"probeset_id": probeset_id, "dataset_name": dataset_name})
        res = cursor.fetchone()
        if res:
            return res[0]
        return None

def retrieve_phenotype_group_name(connection: Any, dataset_id: int):
    """
    Given the dataset id (PublishFreeze.Id in the database), retrieve the name
    of the group the dataset belongs to.
    """
    query = (
        "SELECT iset.Name "
        "FROM InbredSet AS iset "
        "WHERE iset.Id = %(dataset_id)s")
    with connection.cursor() as cursor:
        cursor.execute(query, {"dataset_id": dataset_id})
        res = cursor.fetchone()
        if res:
            return res[0]
        return None

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

def retrieve_dataset_name(
        trait_type: str, threshold: int, dataset_name: str, conn: Any):
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
        "Temp": lambda threshold, dataset_name, conn: {}}
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
    return {
        "searchfield": ["name", "chr"],
	"disfield": ["name", "chr", "mb", "source2", "sequence"],
	"type": "Geno"
    }

def retrieve_publish_trait_dataset():
    """
    Retrieve the dataset that relates to `Publish` traits
    """
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
            trait_type, threshold, trait["db"]["dataset_name"], conn)
    }
    group = retrieve_group_fields(
        trait_type, trait["trait_name"], dataset_name_info, conn)
    return {
        "display_name": dataset_name_info["dataset_name"],
        **dataset_name_info,
        **dataset_fns[trait_type](),
        **group
    }


def retrieve_metadata(name: str) -> dict:
    """Return the full data given a path, NAME"""
    result = {}
    __subject = {
        "summary": "description",
        "tissue": "tissueInfo",
        "specifics": "specifics",
        "cases": "caseInfo",
        "platform": "platformInfo",
        "processing": "processingInfo",
        "notes": "notes",
        "experiment-design": "experimentDesignInfo",
        "acknowledgment": "acknowledgement",
        "citation": "citation",
        "experiment-type": "experimentType",
        "contributors": "contributors",
    }
    for __file in Path(name).glob("*rtf"):
        with __file.open() as _f:
            result[__subject.get(__file.stem, f"gn:{__file.stem}")] = _f.read()
    return result
