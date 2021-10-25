"""
This module will hold functions that are used in the (partial) correlations
feature to access the database to retrieve data needed for computations.
"""

from typing import Any

from gn3.random import random_string
from gn3.db.species import translate_to_mouse_gene_id

def get_filename(target_db_name: str, conn: Any) -> str:
    """
    Retrieve the name of the reference database file with which correlations are
    computed.

    This is a migration of the
    `web.webqtl.correlation.CorrelationPage.getFileName` function in
    GeneNetwork1.
    """
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT Id, FullName from ProbeSetFreeze WHERE Name-%s",
            target_db_name)
        result = cursor.fetchone()
        if result:
            return "ProbeSetFreezeId_{tid}_FullName_{fname}.txt".format(
                tid=result[0],
                fname=result[1].replace(' ', '_').replace('/', '_'))

    return ""

def build_temporary_literature_table(
        species: str, gene_id: int, return_number: int, conn: Any) -> str:
    """
    Build and populate a temporary table to hold the literature correlation data
    to be used in computations.

    "This is a migration of the
    `web.webqtl.correlation.CorrelationPage.getTempLiteratureTable` function in
    GeneNetwork1.
    """
    def __translated_species_id(row, cursor):
        if species == "mouse":
            return row[1]
        query = {
            "rat": "SELECT rat FROM GeneIDXRef WHERE mouse=%s",
            "human": "SELECT human FROM GeneIDXRef WHERE mouse=%d"}
        if species in query.keys():
            cursor.execute(query[species], row[1])
            record = cursor.fetchone()
            if record:
                return record[0]
            return None
        return None

    temp_table_name = f"TOPLITERATURE{random_string(8)}"
    with conn.cursor as cursor:
        mouse_geneid = translate_to_mouse_gene_id(species, gene_id, conn)
        data_query = (
            "SELECT GeneId1, GeneId2, value FROM LCorrRamin3 "
            "WHERE GeneId1 = %(mouse_gene_id)s "
            "UNION ALL "
            "SELECT GeneId2, GeneId1, value FROM LCorrRamin3 "
            "WHERE GeneId2 = %(mouse_gene_id)s "
            "AND GeneId1 != %(mouse_gene_id)s")
        cursor.execute(
            (f"CREATE TEMPORARY TABLE {temp_table_name} ("
             "GeneId1 int(12) unsigned, "
             "GeneId2 int(12) unsigned PRIMARY KEY, "
             "value double)"))
        cursor.execute(data_query, mouse_gene_id=mouse_geneid)
        literature_data = [
            {"GeneId1": row[0], "GeneId2": row[1], "value": row[2]}
            for row in cursor.fetchall()
            if __translated_species_id(row, cursor)]

        cursor.execute(
            (f"INSERT INTO {temp_table_name} "
             "VALUES (%(GeneId1)s, %(GeneId2)s, %(value)s)"),
            literature_data[0:(2 * return_number)])

    return temp_table_name

def fetch_geno_literature_correlations(temp_table: str) -> str:
    """
    Helper function for `fetch_literature_correlations` below, to build query
    for `Geno*` tables.
    """
    return (
        f"SELECT Geno.Name, {temp_table}.value "
        "FROM Geno, GenoXRef, GenoFreeze "
        f"LEFT JOIN {temp_table} ON {temp_table}.GeneId2=ProbeSet.GeneId "
        "WHERE ProbeSet.GeneId IS NOT NULL "
        f"AND {temp_table}.value IS NOT NULL "
        "AND GenoXRef.GenoFreezeId = GenoFreeze.Id "
        "AND GenoFreeze.Name = %(db_name)s "
        "AND Geno.Id=GenoXRef.GenoId "
        "ORDER BY Geno.Id")

def fetch_probeset_literature_correlations(temp_table: str) -> str:
    """
    Helper function for `fetch_literature_correlations` below, to build query
    for `ProbeSet*` tables.
    """
    return (
        f"SELECT ProbeSet.Name, {temp_table}.value "
        "FROM ProbeSet, ProbeSetXRef, ProbeSetFreeze "
        "LEFT JOIN {temp_table} ON {temp_table}.GeneId2=ProbeSet.GeneId "
        "WHERE ProbeSet.GeneId IS NOT NULL "
        "AND {temp_table}.value IS NOT NULL "
        "AND ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id "
        "AND ProbeSetFreeze.Name = %(db_name)s "
        "AND ProbeSet.Id=ProbeSetXRef.ProbeSetId "
        "ORDER BY ProbeSet.Id")

def fetch_literature_correlations(
        species: str, gene_id: int, dataset: dict, return_number: int,
        conn: Any) -> dict:
    """
    Gather the literature correlation data and pair it with trait id string(s).

    This is a migration of the
    `web.webqtl.correlation.CorrelationPage.fetchLitCorrelations` function in
    GeneNetwork1.
    """
    temp_table = build_temporary_literature_table(
        species, gene_id, return_number, conn)
    query_fns = {
        "Geno": fetch_geno_literature_correlations,
        # "Temp": fetch_temp_literature_correlations,
        # "Publish": fetch_publish_literature_correlations,
        "ProbeSet": fetch_probeset_literature_correlations}
    with conn.cursor as cursor:
        cursor.execute(
            query_fns[dataset["dataset_type"]](temp_table),
            db_name=dataset["dataset_name"])
        results = cursor.fetchall()
        cursor.execute("DROP TEMPORARY TABLE %s", temp_table)
        return dict(results) # {trait_name: lit_corr for trait_name, lit_corr in results}
