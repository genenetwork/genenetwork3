"""
This module contains the code and queries for fetching data from the database,
that relates to partial correlations.

It is intended to replace the functions in `gn3.db.traits` and `gn3.db.datasets`
modules with functions that fetch the data enmasse, rather than one at a time.

This module is part of the optimisation effort for the partial correlations.
"""

from functools import reduce, partial
from typing import Any, Dict, Tuple, Union, Sequence, Generator

from MySQLdb.cursors import DictCursor

from gn3.function_helpers import  compose
from gn3.db.traits import (
    build_trait_name,
    with_samplelist_data_setup,
    without_samplelist_data_setup)

def organise_trait_data_by_trait(
        traits_data_rows: Tuple[Dict[str, Any], ...]) -> Dict[
            str, Dict[str, Any]]:
    """
    Organise the trait data items by their trait names.
    """
    def __organise__(acc, row):
        trait_name = row["trait_name"]
        return {
            **acc,
            trait_name: acc.get(trait_name, tuple()) + ({
                key: val for key, val in row.items() if key != "trait_name"},)
        }
    if traits_data_rows:
        return reduce(__organise__, traits_data_rows, {})
    return {}

def temp_traits_data(conn, traits):
    """
    Retrieve trait data for `Temp` traits.
    """
    query = (
        "SELECT "
        "Temp.Name AS trait_name, Strain.Name AS sample_name, TempData.value, "
        "TempData.SE AS se_error, TempData.NStrain AS nstrain, "
        "TempData.Id AS id "
        "FROM TempData, Temp, Strain "
        "WHERE TempData.StrainId = Strain.Id "
        "AND TempData.Id = Temp.DataId "
        f"AND Temp.name IN ({', '.join(['%s'] * len(traits))}) "
        "ORDER BY Strain.Name")
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(
            query,
            tuple(trait["trait_name"] for trait in traits))
        return organise_trait_data_by_trait(cursor.fetchall())
    return {}

def publish_traits_data(conn, traits):
    """
    Retrieve trait data for `Publish` traits.
    """
    dataset_ids = tuple(set(
        trait["db"]["dataset_id"] for trait in traits
        if trait["db"].get("dataset_id") is not None))
    query = (
        "SELECT "
        "PublishXRef.Id AS trait_name, Strain.Name AS sample_name, "
        "PublishData.value, PublishSE.error AS se_error, "
        "NStrain.count AS nstrain, PublishData.Id AS id "
        "FROM (PublishData, Strain, PublishXRef, PublishFreeze) "
        "LEFT JOIN PublishSE "
        "ON (PublishSE.DataId = PublishData.Id "
        "AND PublishSE.StrainId = PublishData.StrainId) "
        "LEFT JOIN NStrain "
        "ON (NStrain.DataId = PublishData.Id "
        "AND NStrain.StrainId = PublishData.StrainId) "
        "WHERE PublishXRef.InbredSetId = PublishFreeze.InbredSetId "
        "AND PublishData.Id = PublishXRef.DataId "
        f"AND PublishXRef.Id  IN ({', '.join(['%s'] * len(traits))}) "
        "AND PublishFreeze.Id IN "
        f"({', '.join(['%s'] * len(dataset_ids))}) "
        "AND PublishData.StrainId = Strain.Id "
        "ORDER BY Strain.Name")
    if len(dataset_ids) > 0:
        with conn.cursor(cursorclass=DictCursor) as cursor:
            cursor.execute(
                query,
                tuple(trait["trait_name"] for trait in traits) +
                tuple(dataset_ids))
            return organise_trait_data_by_trait(cursor.fetchall())
    return {}

def cellid_traits_data(conn, traits):
    """
    Retrieve trait data for `Probe Data` types.
    """
    cellids = tuple(trait["cellid"] for trait in traits)
    dataset_names = set(trait["db"]["dataset_name"] for trait in traits)
    query = (
        "SELECT "
        "ProbeSet.Name AS trait_name, Strain.Name AS sample_name, "
        "ProbeData.value, ProbeSE.error AS se_error, ProbeData.Id AS id "
        "FROM (ProbeData, ProbeFreeze, ProbeSetFreeze, ProbeXRef, Strain, "
        "Probe, ProbeSet) "
        "LEFT JOIN ProbeSE "
        "ON (ProbeSE.DataId = ProbeData.Id "
        "AND ProbeSE.StrainId = ProbeData.StrainId) "
        f"WHERE Probe.Name IN ({', '.join(['%s'] * len(cellids))}) "
        f"AND ProbeSet.Name IN ({', '.join(['%s'] * len(traits))}) "
        "AND Probe.ProbeSetId = ProbeSet.Id "
        "AND ProbeXRef.ProbeId = Probe.Id "
        "AND ProbeXRef.ProbeFreezeId = ProbeFreeze.Id "
        "AND ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id "
        f"AND ProbeSetFreeze.Name IN ({', '.join(['%s'] * len(dataset_names))}) "
        "AND ProbeXRef.DataId = ProbeData.Id "
        "AND ProbeData.StrainId = Strain.Id "
        "ORDER BY Strain.Name")
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(
            query,
            cellids + tuple(trait["trait_name"] for trait in traits) +
            tuple(dataset_names))
        return organise_trait_data_by_trait(cursor.fetchall())
    return {}

def probeset_traits_data(conn, traits):
    """
    Retrieve trait data for `ProbeSet` traits.
    """
    dataset_names = set(trait["db"]["dataset_name"] for trait in traits)
    query = (
        "SELECT ProbeSet.Name AS trait_name, Strain.Name AS sample_name, "
        "ProbeSetData.value, ProbeSetSE.error AS se_error, "
        "ProbeSetData.Id AS id "
        "FROM (ProbeSetData, ProbeSetFreeze, Strain, ProbeSet, ProbeSetXRef) "
        "LEFT JOIN ProbeSetSE ON "
        "(ProbeSetSE.DataId = ProbeSetData.Id "
        "AND ProbeSetSE.StrainId = ProbeSetData.StrainId) "
        f"WHERE ProbeSet.Name IN ({', '.join(['%s'] * len(traits))})"
        "AND ProbeSetXRef.ProbeSetId = ProbeSet.Id "
        "AND ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id "
        f"AND ProbeSetFreeze.Name IN ({', '.join(['%s']*len(dataset_names))}) "
        "AND ProbeSetXRef.DataId = ProbeSetData.Id "
        "AND ProbeSetData.StrainId = Strain.Id "
        "ORDER BY Strain.Name")
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(
            query,
            tuple(trait["trait_name"] for trait in traits) +
            tuple(dataset_names))
        return organise_trait_data_by_trait(cursor.fetchall())
    return {}

def species_ids(conn, traits):
    """
    Retrieve the IDS of the related species from the given list of traits.
    """
    groups = tuple(set(
        trait["db"]["group"] for trait in traits
        if trait["db"].get("group") is not None))
    query = (
        "SELECT Name AS `group`, SpeciesId AS species_id "
        "FROM InbredSet "
        f"WHERE Name IN ({', '.join(['%s'] * len(groups))})")
    if len(groups) > 0:
        with conn.cursor(cursorclass=DictCursor) as cursor:
            cursor.execute(query, groups)
            return tuple(row for row in cursor.fetchall())
    return tuple()

def geno_traits_data(conn, traits):
    """
    Retrieve trait data for `Geno` traits.
    """
    sp_ids = tuple(item["species_id"] for item in species_ids(conn, traits))
    dataset_names = set(trait["db"]["dataset_name"] for trait in traits)
    query = (
        "SELECT Geno.Name AS trait_name, Strain.Name AS sample_name, "
        "GenoData.value, GenoSE.error AS se_error, GenoData.Id AS id "
        "FROM (GenoData, GenoFreeze, Strain, Geno, GenoXRef) "
        "LEFT JOIN GenoSE ON "
        "(GenoSE.DataId = GenoData.Id AND GenoSE.StrainId = GenoData.StrainId) "
        f"WHERE Geno.SpeciesId IN ({', '.join(['%s'] * len(sp_ids))}) "
        f"AND Geno.Name IN ({', '.join(['%s'] * len(traits))}) "
        "AND GenoXRef.GenoId = Geno.Id "
        "AND GenoXRef.GenoFreezeId = GenoFreeze.Id "
        f"AND GenoFreeze.Name IN ({', '.join(['%s'] * len(dataset_names))}) "
        "AND GenoXRef.DataId = GenoData.Id "
        "AND GenoData.StrainId = Strain.Id "
        "ORDER BY Strain.Name")
    if len(sp_ids) > 0 and len(dataset_names) > 0:
        with conn.cursor(cursorclass=DictCursor) as cursor:
            cursor.execute(
                query,
                sp_ids +
                tuple(trait["trait_name"] for trait in traits) +
                tuple(dataset_names))
            return organise_trait_data_by_trait(cursor.fetchall())
    return {}

def traits_data(
        conn: Any, traits: Tuple[Dict[str, Any], ...],
        samplelist: Tuple[str, ...] = tuple()) -> Dict[str, Dict[str, Any]]:
    """
    Retrieve trait data for multiple `traits`

    This is a rework of the `gn3.db.traits.retrieve_trait_data` function.
    """
    def __organise__(acc, trait):
        dataset_type = trait["db"]["dataset_type"]
        if dataset_type == "Temp":
            return {**acc, "Temp": acc.get("Temp", tuple()) + (trait,)}
        if dataset_type == "Publish":
            return {**acc, "Publish": acc.get("Publish", tuple()) + (trait,)}
        if trait.get("cellid"):
            return {**acc, "cellid": acc.get("cellid", tuple()) + (trait,)}
        if dataset_type == "ProbeSet":
            return {**acc, "ProbeSet": acc.get("ProbeSet", tuple()) + (trait,)}
        return {**acc, "Geno": acc.get("Geno", tuple()) + (trait,)}

    def __setup_samplelist__(data):
        if samplelist:
            return tuple(
                item for item in
                map(with_samplelist_data_setup(samplelist), data)
                if item is not None)
        return tuple(
            item for item in
            map(without_samplelist_data_setup(), data)
            if item is not None)

    def __process_results__(results):
        flattened = reduce(lambda acc, res: {**acc, **res}, results)
        return {
            trait_name: {"data": dict(map(
                lambda item: (
                    item["sample_name"],
                    {
                        key: val for key, val in item.items()
                        if item != "sample_name"
                    }),
                __setup_samplelist__(data)))}
            for trait_name, data in flattened.items()}

    traits_data_fns = {
        "Temp": temp_traits_data,
        "Publish": publish_traits_data,
        "cellid": cellid_traits_data,
        "ProbeSet": probeset_traits_data,
        "Geno": geno_traits_data
    }
    return __process_results__(tuple(# type: ignore[var-annotated]
        traits_data_fns[key](conn, vals)
        for key, vals in reduce(__organise__, traits, {}).items()))

def merge_traits_and_info(traits, info_results):
    """
    Utility to merge trait info retrieved from the database with the given traits.
    """
    if info_results:
        results = {
            str(trait["trait_name"]): trait for trait in info_results
        }
        return tuple(
            {
                **trait,
                **results.get(trait["trait_name"], {}),
                "haveinfo": bool(results.get(trait["trait_name"]))
            } for trait in traits)
    return tuple({**trait, "haveinfo": False} for trait in traits)

def publish_traits_info(
        conn: Any, traits: Tuple[Dict[str, Any], ...]) -> Tuple[
            Dict[str, Any], ...]:
    """
    Retrieve trait information for type `Publish` traits.

    This is a rework of `gn3.db.traits.retrieve_publish_trait_info` function:
    this one fetches multiple items in a single query, unlike the original that
    fetches one item per query.
    """
    trait_dataset_ids = set(
        trait["db"]["dataset_id"] for trait in traits
        if trait["db"].get("dataset_id") is not None)
    columns = (
        "PublishXRef.Id, Publication.PubMed_ID, "
        "Phenotype.Pre_publication_description, "
        "Phenotype.Post_publication_description, "
        "Phenotype.Original_description, "
        "Phenotype.Pre_publication_abbreviation, "
        "Phenotype.Post_publication_abbreviation, "
        "Phenotype.Lab_code, Phenotype.Submitter, Phenotype.Owner, "
        "Phenotype.Authorized_Users, "
        "CAST(Publication.Authors AS BINARY) AS Authors, Publication.Title, "
        "Publication.Abstract, Publication.Journal, Publication.Volume, "
        "Publication.Pages, Publication.Month, Publication.Year, "
        "PublishXRef.Sequence, Phenotype.Units, PublishXRef.comments")
    query = (
        "SELECT "
        f"PublishXRef.Id AS trait_name, {columns} "
        "FROM "
        "PublishXRef, Publication, Phenotype, PublishFreeze "
        "WHERE "
        f"PublishXRef.Id IN ({', '.join(['%s'] * len(traits))}) "
        "AND Phenotype.Id = PublishXRef.PhenotypeId "
        "AND Publication.Id = PublishXRef.PublicationId "
        "AND PublishXRef.InbredSetId = PublishFreeze.InbredSetId "
        "AND PublishFreeze.Id IN "
        f"({', '.join(['%s'] * len(trait_dataset_ids))})")
    if trait_dataset_ids:
        with conn.cursor(cursorclass=DictCursor) as cursor:
            cursor.execute(
                query,
                (
                    tuple(trait["trait_name"] for trait in traits) +
                    tuple(trait_dataset_ids)))
            return merge_traits_and_info(traits, cursor.fetchall())
    return tuple({**trait, "haveinfo": False} for trait in traits)

def probeset_traits_info(
        conn: Any, traits: Tuple[Dict[str, Any], ...]):
    """
    Retrieve information for the probeset traits
    """
    dataset_names = set(trait["db"]["dataset_name"] for trait in traits)
    columns = ", ".join(
        [f"ProbeSet.{x}" for x in
         ("name", "symbol", "description", "probe_target_description", "chr",
          "mb", "alias", "geneid", "genbankid", "unigeneid", "omim",
          "refseq_transcriptid", "blatseq", "targetseq", "chipid", "comments",
          "strand_probe", "strand_gene", "probe_set_target_region", "proteinid",
          "probe_set_specificity", "probe_set_blat_score",
          "probe_set_blat_mb_start", "probe_set_blat_mb_end",
          "probe_set_strand", "probe_set_note_by_rw", "flag")])
    query = (
        f"SELECT ProbeSet.Name AS trait_name, {columns} "
        "FROM ProbeSet INNER JOIN ProbeSetXRef "
        "ON ProbeSetXRef.ProbeSetId = ProbeSet.Id "
        "INNER JOIN ProbeSetFreeze "
        "ON ProbeSetFreeze.Id = ProbeSetXRef.ProbeSetFreezeId "
        "WHERE ProbeSetFreeze.Name IN "
        f"({', '.join(['%s'] * len(dataset_names))}) "
        f"AND ProbeSet.Name IN ({', '.join(['%s'] * len(traits))})")
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(
            query,
            tuple(dataset_names) + tuple(
                trait["trait_name"] for trait in traits))
        return merge_traits_and_info(traits, cursor.fetchall())
    return tuple({**trait, "haveinfo": False} for trait in traits)

def geno_traits_info(
        conn: Any, traits: Tuple[Dict[str, Any], ...]):
    """
    Retrieve trait information for type `Geno` traits.

    This is a rework of the `gn3.db.traits.retrieve_geno_trait_info` function.
    """
    dataset_names = set(trait["db"]["dataset_name"] for trait in traits)
    columns = ", ".join([
        f"Geno.{x}" for x in ("name", "chr", "mb", "source2", "sequence")])
    query = (
        "SELECT "
        f"Geno.Name AS trait_name, {columns} "
        "FROM "
        "Geno INNER JOIN GenoXRef ON GenoXRef.GenoId = Geno.Id "
        "INNER JOIN GenoFreeze ON GenoFreeze.Id = GenoXRef.GenoFreezeId "
        f"WHERE GenoFreeze.Name IN ({', '.join(['%s'] * len(dataset_names))}) "
        f"AND Geno.Name IN ({', '.join(['%s'] * len(traits))})")
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(
            query,
            tuple(dataset_names) + tuple(
                trait["trait_name"] for trait in traits))
        return merge_traits_and_info(traits, cursor.fetchall())
    return tuple({**trait, "haveinfo": False} for trait in traits)

def temp_traits_info(
        conn: Any, traits: Tuple[Dict[str, Any], ...]):
    """
    Retrieve trait information for type `Temp` traits.

    A rework of the `gn3.db.traits.retrieve_temp_trait_info` function.
    """
    query = (
        "SELECT Name as trait_name, name, description FROM Temp "
        f"WHERE Name IN ({', '.join(['%s'] * len(traits))})")
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(
            query,
            tuple(trait["trait_name"] for trait in traits))
        return merge_traits_and_info(traits, cursor.fetchall())
    return tuple({**trait, "haveinfo": False} for trait in traits)

def publish_datasets_names(
        conn: Any, threshold: int, dataset_names: Tuple[str, ...]):
    """
    Get the ID, DataScale and various name formats for a `Publish` trait.

    Rework of the `gn3.db.datasets.retrieve_publish_trait_dataset_name`
    """
    query = (
        "SELECT DISTINCT "
        "Id AS dataset_id, Name AS dataset_name, FullName AS dataset_fullname, "
        "ShortName AS dataset_shortname "
        "FROM PublishFreeze "
        "WHERE "
        "public > %s "
        "AND "
        "(Name IN ({names}) OR FullName IN ({names}) OR ShortName IN ({names}))")
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(
            query.format(names=", ".join(["%s"] * len(dataset_names))),
            (threshold,) +(dataset_names * 3))
        return {ds["dataset_name"]: ds for ds in cursor.fetchall()}
    return {}

def set_bxd(group_info):
    """Set the group value to BXD if it is 'BXD300'."""
    return {
        **group_info,
        "group": (
            "BXD" if group_info.get("Name") == "BXD300" else group_info.get("Name", "")),
        "groupid": group_info["Id"]
    }

def organise_groups_by_dataset(
        group_rows: Union[Sequence[Dict[str, Any]], None]) -> Dict[str, Any]:
    """Utility: Organise given groups by their datasets."""
    if group_rows:
        return {
            row["dataset_name"]: set_bxd({
                key: val for key, val in row.items()
                if key != "dataset_name"
            }) for row in group_rows
        }
    return {}

def publish_datasets_groups(conn: Any, dataset_names: Tuple[str]):
    """
    Retrieve the Group, and GroupID values for various Publish trait types.

    Rework of `gn3.db.datasets.retrieve_publish_group_fields` function.
    """
    query = (
        "SELECT PublishFreeze.Name AS dataset_name, InbredSet.Name, "
        "InbredSet.Id "
        "FROM InbredSet, PublishFreeze "
        "WHERE PublishFreeze.InbredSetId = InbredSet.Id "
        f"AND PublishFreeze.Name IN ({', '.join(['%s'] * len(dataset_names))})")
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(query, tuple(dataset_names))
        return organise_groups_by_dataset(cursor.fetchall())
    return {}

def publish_traits_datasets(conn: Any, threshold, traits: Tuple[Dict]):
    """Retrieve datasets for 'Publish' traits."""
    dataset_names = tuple(set(trait["db"]["dataset_name"] for trait in traits))
    dataset_names_info = publish_datasets_names(conn, threshold, dataset_names)
    dataset_groups = publish_datasets_groups(conn, dataset_names) # type: ignore[arg-type]
    return tuple({
        **trait,
        "db": {
            **trait["db"],
            **dataset_names_info.get(trait["db"]["dataset_name"], {}),
            **dataset_groups.get(trait["db"]["dataset_name"], {})
        }
    } for trait in traits)

def probeset_datasets_names(conn: Any, threshold: int, dataset_names: Tuple[str, ...]):
    """
    Get the ID, DataScale and various name formats for a `ProbeSet` trait.
    """
    query = (
        "SELECT Id AS dataset_id, Name AS dataset_name, "
        "FullName AS dataset_fullname, ShortName AS dataset_shortname, "
        "DataScale AS dataset_datascale "
        "FROM ProbeSetFreeze "
        "WHERE "
        "public > %s "
        "AND "
        "(Name IN ({names}) OR FullName IN ({names}) OR ShortName IN ({names}))")
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(
            query.format(names=", ".join(["%s"] * len(dataset_names))),
            (threshold,) +(dataset_names * 3))
        return {ds["dataset_name"]: ds for ds in cursor.fetchall()}
    return {}

def probeset_datasets_groups(conn, dataset_names):
    """
    Retrieve the Group, and GroupID values for various ProbeSet trait types.
    """
    query = (
        "SELECT ProbeSetFreeze.Name AS dataset_name, InbredSet.Name, "
        "InbredSet.Id "
        "FROM InbredSet, ProbeSetFreeze, ProbeFreeze "
        "WHERE ProbeFreeze.InbredSetId = InbredSet.Id "
        "AND ProbeFreeze.Id = ProbeSetFreeze.ProbeFreezeId "
        f"AND ProbeSetFreeze.Name IN ({', '.join(['%s'] * len(dataset_names))})")
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(query, tuple(dataset_names))
        return organise_groups_by_dataset(cursor.fetchall())
    return {}

def probeset_traits_datasets(conn: Any, threshold, traits: Tuple[Dict]):
    """Retrive datasets for 'ProbeSet' traits."""
    dataset_names = tuple(set(trait["db"]["dataset_name"] for trait in traits))
    dataset_names_info = probeset_datasets_names(conn, threshold, dataset_names)
    dataset_groups = probeset_datasets_groups(conn, dataset_names)
    return tuple({
        **trait,
        "db": {
            **trait["db"],
            **dataset_names_info.get(trait["db"]["dataset_name"], {}),
            **dataset_groups.get(trait["db"]["dataset_name"], {})
        }
    } for trait in traits)

def geno_datasets_names(conn, threshold, dataset_names):
    """
    Get the ID, DataScale and various name formats for a `Geno` trait.
    """
    query = (
        "SELECT Id AS dataset_id, Name AS dataset_name, "
        "FullName AS dataset_fullname, ShortName AS dataset_short_name "
        "FROM GenoFreeze "
        "WHERE "
        "public > %s "
        "AND "
        "(Name IN ({names}) OR FullName IN ({names}) OR ShortName IN ({names}))")
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(
            query.format(names=", ".join(["%s"] * len(dataset_names))),
            (threshold,) + (tuple(dataset_names) * 3))
        return {ds["dataset_name"]: ds for ds in cursor.fetchall()}
    return {}

def geno_datasets_groups(conn, dataset_names):
    """
    Retrieve the Group, and GroupID values for various Geno trait types.
    """
    query = (
        "SELECT GenoFreeze.Name AS dataset_name, InbredSet.Name, InbredSet.Id "
        "FROM InbredSet, GenoFreeze "
        "WHERE GenoFreeze.InbredSetId = InbredSet.Id "
        f"AND GenoFreeze.Name IN ({', '.join(['%s'] * len(dataset_names))})")
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(query, tuple(dataset_names))
        return organise_groups_by_dataset(cursor.fetchall())
    return {}

def geno_traits_datasets(conn: Any, threshold: int, traits: Tuple[Dict]):
    """Retrieve datasets for 'Geno' traits."""
    dataset_names = tuple(set(trait["db"]["dataset_name"] for trait in traits))
    dataset_names_info = geno_datasets_names(conn, threshold, dataset_names)
    dataset_groups = geno_datasets_groups(conn, dataset_names)
    return tuple({
        **trait,
        "db": {
            **trait["db"],
            **dataset_names_info.get(trait["db"]["dataset_name"], {}),
            **dataset_groups.get(trait["db"]["dataset_name"], {})
        }
    } for trait in traits)

def temp_datasets_groups(conn, dataset_names):
    """
    Retrieve the Group, and GroupID values for `Temp` trait types.
    """
    query = (
        "SELECT Temp.Name AS dataset_name, InbredSet.Name, InbredSet.Id "
        "FROM InbredSet, Temp "
        "WHERE Temp.InbredSetId = InbredSet.Id "
        f"AND Temp.Name IN ({', '.join(['%s'] * len(dataset_names))})")
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(query, tuple(dataset_names))
        return organise_groups_by_dataset(cursor.fetchall())
    return {}

def temp_traits_datasets(conn: Any, threshold: int, traits: Tuple[Dict]): #pylint: disable=[W0613]
    """
    Retrieve datasets for 'Temp' traits.
    """
    dataset_names = tuple(set(trait["db"]["dataset_name"] for trait in traits))
    dataset_groups = temp_datasets_groups(conn, dataset_names)
    return tuple({
        **trait,
        "db": {
            **trait["db"],
            **dataset_groups.get(trait["db"]["dataset_name"], {})
        }
    } for trait in traits)

def set_confidential(traits):
    """
    Set the confidential field for traits of type `Publish`.
    """
    return tuple({
        **trait,
        "confidential": (
            True if (# pylint: disable=[R1719]
                trait.get("pre_publication_description")
                and not trait.get("pubmed_id"))
            else False)
    } for trait in traits)

def query_qtl_info(conn, query, traits, dataset_ids):
    """
    Utility: Run the `query` to get the QTL information for the given `traits`.
    """
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(
            query,
            tuple(trait["trait_name"] for trait in traits) + dataset_ids)
        results = {
            row["trait_name"]: {
                key: val for key, val in row if key != "trait_name"
            } for row in cursor.fetchall()
        }
        return tuple(
            {**trait, **results.get(trait["trait_name"], {})}
            for trait in traits)

def set_publish_qtl_info(conn, qtl, traits):
    """
    Load extra QTL information for `Publish` traits
    """
    if qtl:
        dataset_ids = set(trait["db"]["dataset_id"] for trait in traits)
        query = (
            "SELECT PublishXRef.Id AS trait_name, PublishXRef.Locus, "
            "PublishXRef.LRS, PublishXRef.additive "
            "FROM PublishXRef, PublishFreeze "
            f"WHERE PublishXRef.Id IN ({', '.join(['%s'] * len(traits))}) "
            "AND PublishXRef.InbredSetId = PublishFreeze.InbredSetId "
            f"AND PublishFreeze.Id IN ({', '.join(['%s'] * len(dataset_ids))})")
        return query_qtl_info(conn, query, traits, tuple(dataset_ids))
    return traits

def set_probeset_qtl_info(conn, qtl, traits):
    """
    Load extra QTL information for `ProbeSet` traits
    """
    if qtl:
        dataset_ids = tuple(set(trait["db"]["dataset_id"] for trait in traits))
        query = (
            "SELECT ProbeSet.Name AS trait_name, ProbeSetXRef.Locus, "
            "ProbeSetXRef.LRS, ProbeSetXRef.pValue, "
            "ProbeSetXRef.mean, ProbeSetXRef.additive "
            "FROM ProbeSetXRef, ProbeSet "
            "WHERE ProbeSetXRef.ProbeSetId = ProbeSet.Id "
            f"AND ProbeSet.Name IN ({', '.join(['%s'] * len(traits))}) "
            "AND ProbeSetXRef.ProbeSetFreezeId IN "
            f"({', '.join(['%s'] * len(dataset_ids))})")
        return query_qtl_info(conn, query, traits, tuple(dataset_ids))
    return traits

def set_sequence(conn, traits):
    """
    Retrieve 'ProbeSet' traits sequence information
    """
    dataset_names = set(trait["db"]["dataset_name"] for trait in traits)
    query = (
        "SELECT ProbeSet.Name as trait_name, ProbeSet.BlatSeq "
        "FROM ProbeSet, ProbeSetFreeze, ProbeSetXRef "
        "WHERE ProbeSet.Id=ProbeSetXRef.ProbeSetId "
        "AND ProbeSetFreeze.Id = ProbeSetXRef.ProbeSetFreezeId "
        f"AND ProbeSet.Name IN ({', '.join(['%s'] * len(traits))}) "
        f"AND ProbeSetFreeze.Name IN ({', '.join(['%s'] * len(dataset_names))})")
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(
            query,
            (tuple(trait["trait_name"] for trait in traits) +
             tuple(dataset_names)))
        results = {
            row["trait_name"]: {
                key: val for key, val in row.items() if key != "trait_name"
            } for row in cursor.fetchall()
        }
        return tuple(
            {
                **trait,
                **results.get(trait["trait_name"], {})
            } for trait in traits)
    return traits

def set_homologene_id(conn, traits):
    """
    Retrieve and set the 'homologene_id' values for ProbeSet traits.
    """
    geneids = set(trait.get("geneid") for trait in traits if trait["haveinfo"])
    groups = set(
        trait["db"].get("group") for trait in traits if trait["haveinfo"])
    if len(geneids) > 1 and len(groups) > 1:
        query = (
            "SELECT InbredSet.Name AS `group`, Homologene.GeneId AS geneid, "
            "HomologeneId "
            "FROM Homologene, Species, InbredSet "
            f"WHERE Homologene.GeneId IN ({', '.join(['%s'] * len(geneids))}) "
            f"AND InbredSet.Name IN ({', '.join(['%s'] * len(groups))}) "
            "AND InbredSet.SpeciesId = Species.Id "
            "AND Species.TaxonomyId = Homologene.TaxonomyId")
        with conn.cursor(cursorclass=DictCursor) as cursor:
            cursor.execute(query, (tuple(geneids) + tuple(groups)))
            results = {
                row["group"]: {
                    row["geneid"]: {
                        key: val for key, val in row.items()
                        if key not in ("group", "geneid")
                    }
                } for row in cursor.fetchall()
            }
            return tuple(
                {
                    **trait, **results.get(
                        trait["db"]["group"], {}).get(trait["geneid"], {})
                } for trait in traits)
    return traits

def traits_datasets(conn, threshold, traits):
    """
    Retrieve datasets for various `traits`.
    """
    dataset_fns = {
        "Temp": temp_traits_datasets,
        "Geno": geno_traits_datasets,
        "Publish": publish_traits_datasets,
        "ProbeSet": probeset_traits_datasets
    }
    def __organise_by_type__(acc, trait):
        dataset_type = trait["db"]["dataset_type"]
        return {
            **acc,
            dataset_type: acc.get(dataset_type, tuple()) + (trait,)
        }
    with_datasets = {
        trait["trait_fullname"]: trait for trait in (
            item for sublist in (
                dataset_fns[dtype](conn, threshold, ttraits)
                for dtype, ttraits
                in reduce(__organise_by_type__, traits, {}).items())
            for item in sublist)}
    return tuple(
        {**trait, **with_datasets.get(trait["trait_fullname"], {})}
        for trait in traits)

def traits_info(
        conn: Any, threshold: int, traits_fullnames: Tuple[str, ...],
        qtl=None) -> Generator:
    """
    Retrieve basic trait information for multiple `traits`.

    This is a rework of the `gn3.db.traits.retrieve_trait_info` function.
    """
    def __organise_by_dataset_type__(acc, trait):
        dataset_type = trait["db"]["dataset_type"]
        return {
            **acc,
            dataset_type: acc.get(dataset_type, tuple()) + (trait,)
        }
    traits = traits_datasets(
        conn, threshold,
        tuple(build_trait_name(trait) for trait in traits_fullnames))
    traits_fns = {
        "Publish": compose(
            set_confidential, partial(set_publish_qtl_info, conn, qtl),
            partial(publish_traits_info, conn),
            partial(publish_traits_datasets, conn, threshold)),
        "ProbeSet": compose(
            partial(set_sequence, conn),
            partial(set_probeset_qtl_info, conn, qtl),
            partial(set_homologene_id, conn),
            partial(probeset_traits_info, conn),
            partial(probeset_traits_datasets, conn, threshold)),
        "Geno": compose(
            partial(geno_traits_info, conn),
            partial(geno_traits_datasets, conn, threshold)),
        "Temp": compose(
            partial(temp_traits_info, conn),
            partial(temp_traits_datasets, conn, threshold))
    }
    return (
        trait for sublist in (# type: ignore[var-annotated]
            traits_fns[dataset_type](traits)
            for dataset_type, traits
            in reduce(__organise_by_dataset_type__, traits, {}).items())
        for trait in sublist)
