"""
This module will hold functions that are used in the (partial) correlations
feature to access the database to retrieve data needed for computations.
"""

from functools import reduce
from typing import Any, Dict, Tuple

from gn3.random import random_string
from gn3.data_helpers import partition_all
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
        return dict(results)

def compare_tissue_correlation_absolute_values(val1, val2):
    """
    Comparison function for use when sorting tissue correlation values.

    This is a partial migration of the
    `web.webqtl.correlation.CorrelationPage.getTempTissueCorrTable` function in
    GeneNetwork1."""
    try:
        if abs(val1) < abs(val2):
            return 1
        if abs(val1) == abs(val2):
            return 0
        return -1
    except TypeError:
        return 0

def fetch_symbol_value_pair_dict(
        symbol_list: Tuple[str, ...], data_id_dict: dict,
        conn: Any) -> Dict[str, Tuple[float, ...]]:
    """
    Map each gene symbols to the corresponding tissue expression data.

    This is a migration of the
    `web.webqtl.correlation.correlationFunction.getSymbolValuePairDict` function
    in GeneNetwork1.
    """
    data_ids = {
        symbol: data_id_dict.get(symbol) for symbol in symbol_list
        if data_id_dict.get(symbol) is not None
    }
    query = "SELECT Id, value FROM TissueProbeSetData WHERE Id IN %(data_ids)s"
    with conn.cursor() as cursor:
        cursor.execute(
            query,
            data_ids=tuple(data_ids.values()))
        value_results = cursor.fetchall()
        return {
            key: tuple(row[1] for row in value_results if row[0] == key)
            for key in data_ids.keys()
        }

    return {}

def fetch_gene_symbol_tissue_value_dict(
        symbol_list: Tuple[str, ...], data_id_dict: dict, conn: Any,
        limit_num: int = 1000) -> dict:#getGeneSymbolTissueValueDict
    """
    Wrapper function for `gn3.db.correlations.fetch_symbol_value_pair_dict`.

    This is a migrations of the
    `web.webqtl.correlation.correlationFunction.getGeneSymbolTissueValueDict` in
    GeneNetwork1.
    """
    count = len(symbol_list)
    if count != 0 and count <= limit_num:
        return fetch_symbol_value_pair_dict(symbol_list, data_id_dict, conn)

    if count > limit_num:
        return {
            key: value for dct in [
                fetch_symbol_value_pair_dict(sl, data_id_dict, conn)
                for sl in partition_all(limit_num, symbol_list)]
            for key, value in dct.items()
        }

    return {}

def fetch_tissue_probeset_xref_info(
        gene_name_list: Tuple[str, ...], probeset_freeze_id: int,
        conn: Any) -> Tuple[tuple, dict, dict, dict, dict, dict, dict]:
    """
    Retrieve the ProbeSet XRef information for tissues.

    This is a migration of the
    `web.webqtl.correlation.correlationFunction.getTissueProbeSetXRefInfo`
    function in GeneNetwork1."""
    with conn.cursor() as cursor:
        if len(gene_name_list) == 0:
            query = (
                "SELECT t.Symbol, t.GeneId, t.DataId, t.Chr, t.Mb, "
                "t.description, t.Probe_Target_Description "
                "FROM "
                "("
                "  SELECT Symbol, max(Mean) AS maxmean "
                "  FROM TissueProbeSetXRef "
                "  WHERE TissueProbeSetFreezeId=%(probeset_freeze_id)s "
                "  AND Symbol != '' "
                "  AND Symbol IS NOT NULL "
                "  GROUP BY Symbol"
                ") AS x "
                "INNER JOIN TissueProbeSetXRef AS t ON t.Symbol = x.Symbol "
                "AND t.Mean = x.maxmean")
            cursor.execute(query, probeset_freeze_id=probeset_freeze_id)
        else:
            query = (
                "SELECT t.Symbol, t.GeneId, t.DataId, t.Chr, t.Mb, "
                "t.description, t.Probe_Target_Description "
                "FROM "
                "("
                "  SELECT Symbol, max(Mean) AS maxmean "
                "  FROM TissueProbeSetXRef "
                "  WHERE TissueProbeSetFreezeId=%(probeset_freeze_id)s "
                "  AND Symbol in %(symbols)s "
                "  GROUP BY Symbol"
                ") AS x "
                "INNER JOIN TissueProbeSetXRef AS t ON t.Symbol = x.Symbol "
                "AND t.Mean = x.maxmean")
            cursor.execute(
                query, probeset_freeze_id=probeset_freeze_id,
                symbols=tuple(gene_name_list))

        results = cursor.fetchall()

    return reduce(
        lambda acc, item: (
            acc[0] + (item[0],),
            {**acc[1], item[0].lower(): item[1]},
            {**acc[1], item[0].lower(): item[2]},
            {**acc[1], item[0].lower(): item[3]},
            {**acc[1], item[0].lower(): item[4]},
            {**acc[1], item[0].lower(): item[5]},
            {**acc[1], item[0].lower(): item[6]}),
        results or tuple(),
        (tuple(), {}, {}, {}, {}, {}, {}))

def correlations_of_all_tissue_traits() -> Tuple[dict, dict]:
def fetch_gene_symbol_tissue_value_dict_for_trait(
        gene_name_list: Tuple[str, ...], probeset_freeze_id: int,
        conn: Any) -> dict:
    """
    Fetches a map of the gene symbols to the tissue values.

    This is a migration of the
    `web.webqtl.correlation.correlationFunction.getGeneSymbolTissueValueDictForTrait`
    function in GeneNetwork1.
    """
    xref_info = fetch_tissue_probeset_xref_info(
        gene_name_list, probeset_freeze_id, conn)
    if xref_info[0]:
        return fetch_gene_symbol_tissue_value_dict(xref_info[0], xref_info[2], conn)
    return {}

    This is a migration of the
    `web.webqtl.correlation.CorrelationPage.calculateCorrOfAllTissueTrait`
    function in GeneNetwork1.
    """
    raise Exception("Unimplemented!!!")
    return ({}, {})

def build_temporary_tissue_correlations_table(
        trait_symbol: str, probeset_freeze_id: int, method: str,
        return_number: int, conn: Any) -> str:
    """
    Build a temporary table to hold the tissue correlations data.

    This is a migration of the
    `web.webqtl.correlation.CorrelationPage.getTempTissueCorrTable` function in
    GeneNetwork1."""
    raise Exception("Unimplemented!!!")
    return ""

def fetch_tissue_correlations(
        dataset: dict, trait_symbol: str, probeset_freeze_id: int, method: str,
        return_number: int, conn: Any) -> dict:
    """
    Pair tissue correlations data with a trait id string.

    This is a migration of the
    `web.webqtl.correlation.CorrelationPage.fetchTissueCorrelations` function in
    GeneNetwork1.
    """
    temp_table = build_temporary_tissue_correlations_table(
        trait_symbol, probeset_freeze_id, method, return_number, conn)
    with conn.cursor() as cursor:
        cursor.execute(
            (
                f"SELECT ProbeSet.Name, {temp_table}.Correlation, "
                f"{temp_table}.PValue "
                "FROM (ProbeSet, ProbeSetXRef, ProbeSetFreeze) "
                "LEFT JOIN {temp_table} ON {temp_table}.Symbol=ProbeSet.Symbol "
                "WHERE ProbeSetFreeze.Name = %(db_name) "
                "AND ProbeSetFreeze.Id=ProbeSetXRef.ProbeSetFreezeId "
                "AND ProbeSet.Id = ProbeSetXRef.ProbeSetId "
                "AND ProbeSet.Symbol IS NOT NULL "
                "AND %s.Correlation IS NOT NULL"),
            db_name=dataset["dataset_name"])
        results = cursor.fetchall()
        cursor.execute("DROP TEMPORARY TABLE %s", temp_table)
        return {
            trait_name: (tiss_corr, tiss_p_val)
            for trait_name, tiss_corr, tiss_p_val in results}
