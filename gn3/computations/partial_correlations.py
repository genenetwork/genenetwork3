"""
This module deals with partial correlations.

It is an attempt to migrate over the partial correlations feature from
GeneNetwork1.
"""

import math
import warnings
from functools import reduce, partial
from typing import Any, Tuple, Union, Sequence

import numpy
import pandas
import pingouin
from scipy.stats import pearsonr, spearmanr

from gn3.settings import TEXTDIR
from gn3.random import random_string
from gn3.function_helpers import  compose
from gn3.data_helpers import parse_csv_line
from gn3.db.traits import export_informative
from gn3.db.datasets import retrieve_trait_dataset
from gn3.db.partial_correlations import traits_info, traits_data
from gn3.db.species import species_name, translate_to_mouse_gene_id
from gn3.db.correlations import (
    get_filename,
    fetch_all_database_data,
    check_for_literature_info,
    fetch_tissue_correlations,
    fetch_literature_correlations,
    check_symbol_for_tissue_correlation,
    fetch_gene_symbol_tissue_value_dict_for_trait)

def control_samples(controls: Sequence[dict], sampleslist: Sequence[str]):
    """
    Fetches data for the control traits.

    This migrates `web/webqtl/correlation/correlationFunction.controlStrain` in
    GN1, with a few modifications to the arguments passed in.

    PARAMETERS:
    controls: A map of sample names to trait data. Equivalent to the `cvals`
        value in the corresponding source function in GN1.
    sampleslist: A list of samples. Equivalent to `strainlst` in the
        corresponding source function in GN1
    """
    def __process_control__(trait_data):
        def __process_sample__(acc, sample):
            if sample in trait_data["data"].keys():
                sample_item = trait_data["data"][sample]
                val = sample_item["value"]
                if val is not None:
                    return (
                        acc[0] + (sample,),
                        acc[1] + (val,),
                        acc[2] + (sample_item["variance"],))
            return acc
        return reduce(
            __process_sample__, sampleslist, (tuple(), tuple(), tuple()))

    return reduce(
        lambda acc, item: (
            acc[0] + (item[0],),
            acc[1] + (item[1],),
            acc[2] + (item[2],),
            acc[3] + (len(item[0]),),
        ),
        [__process_control__(trait_data) for trait_data in controls],
        (tuple(), tuple(), tuple(), tuple()))

def dictify_by_samples(samples_vals_vars: Sequence[Sequence]) -> Sequence[dict]:
    """
    Build a sequence of dictionaries from a sequence of separate sequences of
    samples, values and variances.

    This is a partial migration of
    `web.webqtl.correlation.correlationFunction.fixStrains` function in GN1.
    This implementation extracts code that will find common use, and that will
    find use in more than one place.
    """
    def __build_key_value_pairs__(
            sample: str, value: Union[float, None],
            variance: Union[float, None]) -> dict[
                str, dict[str, Union[str, float, None]]]:
        smp = sample.strip()
        if smp == "":
            warnings.warn(
                "Empty strings for sample names is not allowed. Returning None",
                category=RuntimeWarning)
            return None
        return (smp, {"sample_name": smp, "value": value, "variance": variance})

    return tuple(
        dict(item for item in
             (__build_key_value_pairs__(sample, val, var)
              for sample, val, var in zip(*trait_line))
             if item is not None)
        for trait_line in zip(*(samples_vals_vars[0:3])))

def fix_samples(primary_trait: dict, control_traits: Sequence[dict]) -> Sequence[Sequence[Any]]:
    """
    Corrects sample_names, values and variance such that they all contain only
    those samples that are common to the reference trait and all control traits.

    This is a partial migration of the
    `web.webqtl.correlation.correlationFunction.fixStrain` function in GN1.
    """
    primary_samples = tuple(
        present[0] for present in
        ((sample, all(sample in control.keys() for control in control_traits))
         for sample in primary_trait.keys())
        if present[1])
    control_vals_vars: tuple = reduce(
        lambda acc, x: (acc[0] + (x[0],), acc[1] + (x[1],)),
        ((item["value"], item["variance"])
         for sublist in [tuple(control.values()) for control in control_traits]
         for item in sublist),
        (tuple(), tuple()))
    return (
        primary_samples,
        tuple(primary_trait[sample]["value"] for sample in primary_samples),
        control_vals_vars[0],
        tuple(primary_trait[sample]["variance"] for sample in primary_samples),
        control_vals_vars[1])

def find_identical_traits(
        primary_name: str, primary_value: float, control_names: Tuple[str, ...],
        control_values: Tuple[float, ...]) -> Tuple[str, ...]:
    """
    Find traits that have the same value when the values are considered to
    3 decimal places.

    This is a migration of the
    `web.webqtl.correlation.correlationFunction.findIdenticalTraits` function in
    GN1.
    """
    def __merge_identicals__(
            acc: Tuple[str, ...],
            ident: Tuple[str, Tuple[str, ...]]) -> Tuple[str, ...]:
        return acc + ident[1]

    def __dictify_controls__(acc, control_item):
        ckey = tuple("{:.3f}".format(item) for item in control_item[0])
        return {**acc, ckey: acc.get(ckey, tuple()) + (control_item[1],)}

    return (reduce(## for identical control traits
        __merge_identicals__,
        (item for item in reduce(# type: ignore[var-annotated]
            __dictify_controls__, zip(control_values, control_names),
            {}).items() if len(item[1]) > 1),
        tuple())
            or
            reduce(## If no identical control traits, try primary and controls
                __merge_identicals__,
                (item for item in reduce(# type: ignore[var-annotated]
                    __dictify_controls__,
                    zip((primary_value,) + control_values,
                        (primary_name,) + control_names), {}).items()
                 if len(item[1]) > 1),
                tuple()))

def tissue_correlation(
        primary_trait_values: Tuple[float, ...],
        target_trait_values: Tuple[float, ...],
        method: str) -> Tuple[float, float]:
    """
    Compute the correlation between the primary trait values, and the values of
    a single target value.

    This migrates the `cal_tissue_corr` function embedded in the larger
    `web.webqtl.correlation.correlationFunction.batchCalTissueCorr` function in
    GeneNetwork1.
    """
    def spearman_corr(*args):
        result = spearmanr(*args)
        return (result.correlation, result.pvalue)

    method_fns = {"pearson": pearsonr, "spearman": spearman_corr}

    assert len(primary_trait_values) == len(target_trait_values), (
        "The lengths of the `primary_trait_values` and `target_trait_values` "
        "must be equal")
    assert method in method_fns.keys(), (
        "Method must be one of: {}".format(",".join(method_fns.keys())))

    corr, pvalue = method_fns[method](primary_trait_values, target_trait_values)
    return (corr, pvalue)

def batch_computed_tissue_correlation(
        primary_trait_values: Tuple[float, ...], target_traits_dict: dict,
        method: str) -> Tuple[dict, dict]:
    """
    This is a migration of the
    `web.webqtl.correlation.correlationFunction.batchCalTissueCorr` function in
    GeneNetwork1
    """
    def __corr__(acc, target):
        corr = tissue_correlation(primary_trait_values, target[1], method)
        return ({**acc[0], target[0]: corr[0]}, {**acc[0], target[1]: corr[1]})
    return reduce(__corr__, target_traits_dict.items(), ({}, {}))

def correlations_of_all_tissue_traits(
        primary_trait_symbol_value_dict: dict, symbol_value_dict: dict,
        method: str) -> Tuple[dict, dict]:
    """
    Computes and returns the correlation of all tissue traits.

    This is a migration of the
    `web.webqtl.correlation.correlationFunction.calculateCorrOfAllTissueTrait`
    function in GeneNetwork1.
    """
    primary_trait_values = tuple(primary_trait_symbol_value_dict.values())[0]
    return batch_computed_tissue_correlation(
        primary_trait_values, symbol_value_dict, method)

def good_dataset_samples_indexes(
        samples: Tuple[str, ...],
        samples_from_file: Tuple[str, ...]) -> Tuple[int, ...]:
    """
    Return the indexes of the items in `samples_from_files` that are also found
    in `samples`.

    This is a partial migration of the
    `web.webqtl.correlation.PartialCorrDBPage.getPartialCorrelationsFast`
    function in GeneNetwork1.
    """
    return tuple(sorted(
        samples_from_file.index(good) for good in
        set(samples).intersection(set(samples_from_file))))

def partial_correlations_fast(# pylint: disable=[R0913, R0914]
        samples, primary_vals, control_vals, database_filename,
        fetched_correlations, method: str, correlation_type: str) -> Tuple[
            int, Tuple[float, ...]]:
    """
    Computes partial correlation coefficients using data from a CSV file.

    This is a partial migration of the
    `web.webqtl.correlation.PartialCorrDBPage.getPartialCorrelationsFast`
    function in GeneNetwork1.
    """
    assert method in ("spearman", "pearson")
    with open(database_filename, "r") as dataset_file:
        dataset = tuple(dataset_file.readlines())

    good_dataset_samples = good_dataset_samples_indexes(
        samples, parse_csv_line(dataset[0])[1:])

    def __process_trait_names_and_values__(acc, line):
        trait_line = parse_csv_line(line)
        trait_name = trait_line[0]
        trait_data = trait_line[1:]
        if trait_name in fetched_correlations.keys():
            return (
                acc[0] + (trait_name,),
                acc[1] + tuple(
                    trait_data[i] if i in good_dataset_samples else None
                    for i in range(len(trait_data))))
        return acc

    processed_trait_names_values: tuple = reduce(
        __process_trait_names_and_values__, dataset[1:], (tuple(), tuple()))
    all_target_trait_names: Tuple[str, ...] = processed_trait_names_values[0]
    all_target_trait_values: Tuple[float, ...] = processed_trait_names_values[1]

    all_correlations = compute_partial(
        primary_vals, control_vals, all_target_trait_names,
        all_target_trait_values, method)
    ## Line 772 to 779 in GN1 are the cause of the weird complexity in the
    ## return below. Once the surrounding code is successfully migrated and
    ## reworked, this complexity might go away, by getting rid of the
    ## `correlation_type` parameter
    return len(all_correlations), tuple(
        corr + (
            (fetched_correlations[corr[0]],) # type: ignore[index]
            if correlation_type == "literature"
            else fetched_correlations[corr[0]][0:2]) # type: ignore[index]
        for idx, corr in enumerate(all_correlations))

def build_data_frame(
        xdata: Tuple[float, ...], ydata: Tuple[float, ...],
        zdata: Union[
            Tuple[float, ...],
            Tuple[Tuple[float, ...], ...]]) -> pandas.DataFrame:
    """
    Build a pandas DataFrame object from xdata, ydata and zdata
    """
    x_y_df = pandas.DataFrame({"x": xdata, "y": ydata})
    if isinstance(zdata[0], float):
        return x_y_df.join(pandas.DataFrame({"z": zdata}))
    interm_df = x_y_df.join(pandas.DataFrame(
        {"z{}".format(i): val for i, val in enumerate(zdata)}))
    if interm_df.shape[1] == 3:
        return interm_df.rename(columns={"z0": "z"})
    return interm_df

def compute_trait_info(primary_vals, control_vals, target, method):
    targ_vals = target[0]
    targ_name = target[1]
    primary = [
        prim for targ, prim in zip(targ_vals, primary_vals)
        if targ is not None]

    if len(primary) < 3:
        return None

    def __remove_controls_for_target_nones(cont_targ):
        return tuple(cont for cont, targ in cont_targ if targ is not None)

    datafrm = build_data_frame(
        primary,
        [targ for targ in targ_vals if targ is not None],
        [__remove_controls_for_target_nones(tuple(zip(control, targ_vals)))
         for control in control_vals])
    covariates = "z" if datafrm.shape[1] == 3 else [
        col for col in datafrm.columns if col not in ("x", "y")]
    ppc = pingouin.partial_corr(
        data=datafrm, x="x", y="y", covar=covariates, method=(
            "pearson" if "pearson" in method.lower() else "spearman"))
    pc_coeff = ppc["r"][0]

    zero_order_corr = pingouin.corr(
        datafrm["x"], datafrm["y"], method=(
            "pearson" if "pearson" in method.lower() else "spearman"))

    if math.isnan(pc_coeff):
        return (
            targ_name, len(primary), pc_coeff, 1, zero_order_corr["r"][0],
            zero_order_corr["p-val"][0])
    return (
        targ_name, len(primary), pc_coeff,
        (ppc["p-val"][0] if not math.isnan(ppc["p-val"][0]) else (
            0 if (abs(pc_coeff - 1) < 0.0000001) else 1)),
        zero_order_corr["r"][0], zero_order_corr["p-val"][0])

def compute_partial(
        primary_vals, control_vals, target_vals, target_names,
        method: str) -> Tuple[
            Union[
                Tuple[str, int, float, float, float, float], None],
            ...]:
    """
    Compute the partial correlations.

    This is a re-implementation of the
    `web.webqtl.correlation.correlationFunction.determinePartialsByR` function
    in GeneNetwork1.

    This implementation reworks the child function `compute_partial` which will
    then be used in the place of `determinPartialsByR`.
    """
    return tuple(
        result for result in (
            compute_trait_info(
                primary_vals, control_vals, (tvals, tname), method)
            for tvals, tname in zip(target_vals, target_names))
        if result is not None)

def partial_correlations_normal(# pylint: disable=R0913
        primary_vals, control_vals, input_trait_gene_id, trait_database,
        data_start_pos: int, db_type: str, method: str) -> Tuple[
            int, Tuple[Union[
                Tuple[str, int, float, float, float, float], None],
                       ...]]:#Tuple[float, ...]
    """
    Computes the correlation coefficients.

    This is a migration of the
    `web.webqtl.correlation.PartialCorrDBPage.getPartialCorrelationsNormal`
    function in GeneNetwork1.
    """
    def __add_lit_and_tiss_corr__(item):
        if method.lower() == "sgo literature correlation":
            # if method is 'SGO Literature Correlation', `compute_partial`
            # would give us LitCorr in the [1] position
            return tuple(item) + trait_database[1]
        if method.lower() in (
                "tissue correlation, pearson's r",
                "tissue correlation, spearman's rho"):
            # if method is 'Tissue Correlation, *', `compute_partial` would give
            # us Tissue Corr in the [1] position and Tissue Corr P Value in the
            # [2] position
            return tuple(item) + (trait_database[1], trait_database[2])
        return item

    target_trait_names, target_trait_vals = reduce(# type: ignore[var-annotated]
        lambda acc, item: (acc[0]+(item[0],), acc[1]+(item[data_start_pos:],)),
        trait_database, (tuple(), tuple()))

    all_correlations = compute_partial(
        primary_vals, control_vals, target_trait_vals, target_trait_names,
        method)

    if (input_trait_gene_id and db_type == "ProbeSet" and method.lower() in (
            "sgo literature correlation", "tissue correlation, pearson's r",
            "tissue correlation, spearman's rho")):
        return (
            len(trait_database),
            tuple(
                __add_lit_and_tiss_corr__(item)
                for idx, item in enumerate(all_correlations)))

    return len(trait_database), all_correlations

def partial_corrs(# pylint: disable=[R0913]
        conn, samples, primary_vals, control_vals, return_number, species,
        input_trait_geneid, input_trait_symbol, tissue_probeset_freeze_id,
        method, dataset, database_filename):
    """
    Compute the partial correlations, selecting the fast or normal method
    depending on the existence of the database text file.

    This is a partial migration of the
    `web.webqtl.correlation.PartialCorrDBPage.__init__` function in
    GeneNetwork1.
    """
    if database_filename:
        return partial_correlations_fast(
            samples, primary_vals, control_vals, database_filename,
            (
                fetch_literature_correlations(
                    species, input_trait_geneid, dataset, return_number, conn)
                if "literature" in method.lower() else
                fetch_tissue_correlations(
                    dataset, input_trait_symbol, tissue_probeset_freeze_id,
                    method, return_number, conn)),
            method,
            ("literature" if method.lower() == "sgo literature correlation"
             else ("tissue" if "tissue" in method.lower() else "genetic")))

    trait_database, data_start_pos = fetch_all_database_data(
        conn, species, input_trait_geneid, input_trait_symbol, samples, dataset,
        method, return_number, tissue_probeset_freeze_id)
    return partial_correlations_normal(
        primary_vals, control_vals, input_trait_geneid, trait_database,
        data_start_pos, dataset, method)

def literature_correlation_by_list(
        conn: Any, species: str, trait_list: Tuple[dict]) -> Tuple[dict, ...]:
    """
    This is a migration of the
    `web.webqtl.correlation.CorrelationPage.getLiteratureCorrelationByList`
    function in GeneNetwork1.
    """
    if any((lambda t: (
            bool(t.get("tissue_corr")) and
            bool(t.get("tissue_p_value"))))(trait)
           for trait in trait_list):
        temporary_table_name = f"LITERATURE{random_string(8)}"
        query1 = (
            f"CREATE TEMPORARY TABLE {temporary_table_name} "
            "(GeneId1 INT(12) UNSIGNED, GeneId2 INT(12) UNSIGNED PRIMARY KEY, "
            "value DOUBLE)")
        query2 = (
            f"INSERT INTO {temporary_table_name}(GeneId1, GeneId2, value) "
            "SELECT GeneId1, GeneId2, value FROM LCorrRamin3 "
            "WHERE GeneId1=%(geneid)s")
        query3 = (
            "INSERT INTO {temporary_table_name}(GeneId1, GeneId2, value) "
            "SELECT GeneId2, GeneId1, value FROM LCorrRamin3 "
            "WHERE GeneId2=%s AND GeneId1 != %(geneid)s")

        def __set_mouse_geneid__(trait):
            if trait.get("geneid"):
                return {
                    **trait,
                    "mouse_geneid": translate_to_mouse_gene_id(
                        species, trait.get("geneid"), conn)
                }
            return {**trait, "mouse_geneid": 0}

        def __retrieve_lcorr__(cursor, geneids):
            cursor.execute(
                f"SELECT GeneId2, value FROM {temporary_table_name} "
                "WHERE GeneId2 IN %(geneids)s",
                geneids=geneids)
            return dict(cursor.fetchall())

        with conn.cursor() as cursor:
            cursor.execute(query1)
            cursor.execute(query2)
            cursor.execute(query3)

            traits = tuple(__set_mouse_geneid__(trait) for trait in trait_list)
            lcorrs = __retrieve_lcorr__(
                cursor, (
                    trait["mouse_geneid"] for trait in traits
                    if (trait["mouse_geneid"] != 0 and
                        trait["mouse_geneid"].find(";") < 0)))
            return tuple(
                {**trait, "l_corr": lcorrs.get(trait["mouse_geneid"], None)}
                for trait in traits)

        return trait_list
    return trait_list

def tissue_correlation_by_list(
        conn: Any, primary_trait_symbol: str, tissue_probeset_freeze_id: int,
        method: str, trait_list: Tuple[dict]) -> Tuple[dict, ...]:
    """
    This is a migration of the
    `web.webqtl.correlation.CorrelationPage.getTissueCorrelationByList`
    function in GeneNetwork1.
    """
    def __add_tissue_corr__(trait, primary_trait_values, trait_values):
        result = pingouin.corr(
            primary_trait_values, trait_values,
            method=("spearman" if "spearman" in method.lower() else "pearson"))
        return {
            **trait,
            "tissue_corr": result["r"],
            "tissue_p_value": result["p-val"]
        }

    if any((lambda t: bool(t.get("l_corr")))(trait) for trait in trait_list):
        prim_trait_symbol_value_dict = fetch_gene_symbol_tissue_value_dict_for_trait(
            (primary_trait_symbol,), tissue_probeset_freeze_id, conn)
        if primary_trait_symbol.lower() in prim_trait_symbol_value_dict:
            primary_trait_value = prim_trait_symbol_value_dict[
                primary_trait_symbol.lower()]
            gene_symbol_list = tuple(
                trait["symbol"] for trait in trait_list if "symbol" in trait.keys())
            symbol_value_dict = fetch_gene_symbol_tissue_value_dict_for_trait(
                gene_symbol_list, tissue_probeset_freeze_id, conn)
            return tuple(
                __add_tissue_corr__(
                    trait, primary_trait_value,
                    symbol_value_dict[trait["symbol"].lower()])
                for trait in trait_list
                if ("symbol" in trait and
                    bool(trait["symbol"]) and
                    trait["symbol"].lower() in symbol_value_dict))
        return tuple({
            **trait,
            "tissue_corr": None,
            "tissue_p_value": None
        } for trait in trait_list)
    return trait_list

def trait_for_output(trait):
    """
    Process a trait for output.

    Removes a lot of extraneous data from the trait, that is not needed for
    the display of partial correlation results.
    This function also removes all key-value pairs, for which the value is
    `None`, because it is a waste of network resources to transmit the key-value
    pair just to indicate it does not exist.
    """
    def __nan_to_none__(val):
        if val is None:
            return None
        if math.isnan(val) or numpy.isnan(val):
            return None
        return val

    trait = {
        "trait_type": trait["db"]["dataset_type"],
        "dataset_name": trait["db"]["dataset_name"],
        "dataset_type": trait["db"]["dataset_type"],
        "group": trait["db"]["group"],
        "trait_fullname": trait["trait_fullname"],
        "trait_name": trait["trait_name"],
        "symbol": trait.get("symbol"),
        "description": trait.get("description"),
        "pre_publication_description": trait.get("Pre_publication_description"),
        "post_publication_description": trait.get(
            "Post_publication_description"),
        "original_description": trait.get("Original_description"),
        "authors": trait.get("Authors"),
        "year": trait.get("Year"),
        "probe_target_description": trait.get("Probe_target_description"),
        "chr": trait.get("chr"),
        "mb": trait.get("mb"),
        "geneid": trait.get("geneid"),
        "homologeneid": trait.get("homologeneid"),
        "noverlap": trait.get("noverlap"),
        "partial_corr": __nan_to_none__(trait.get("partial_corr")),
        "partial_corr_p_value": __nan_to_none__(
            trait.get("partial_corr_p_value")),
        "corr": __nan_to_none__(trait.get("corr")),
        "corr_p_value": __nan_to_none__(trait.get("corr_p_value")),
        "rank_order": __nan_to_none__(trait.get("rank_order")),
        "delta": (
            None if trait.get("partial_corr") is None
            else (trait.get("partial_corr") - trait.get("corr"))),
        "l_corr": __nan_to_none__(trait.get("l_corr")),
        "tissue_corr": __nan_to_none__(trait.get("tissue_corr")),
        "tissue_p_value": __nan_to_none__(trait.get("tissue_p_value"))
    }
    return {key: val for key, val in trait.items() if val is not None}

def partial_correlations_entry(# pylint: disable=[R0913, R0914, R0911]
        conn: Any, primary_trait_name: str,
        control_trait_names: Tuple[str, ...], method: str,
        criteria: int, target_db_name: str) -> dict:
    """
    This is the 'ochestration' function for the partial-correlation feature.

    This function will dispatch the functions doing data fetches from the
    database (and various other places) and feed that data to the functions
    doing the conversions and computations. It will then return the results of
    all of that work.

    This function is doing way too much. Look into splitting out the
    functionality into smaller functions that do fewer things.
    """
    threshold = 0
    corr_min_informative = 4

    all_traits = traits_info(
        conn, threshold, (primary_trait_name,) + control_trait_names)
    all_traits_data = traits_data(conn, all_traits)

    primary_trait = tuple(
        trait for trait in all_traits
        if trait["trait_fullname"] == primary_trait_name)[0]
    if not primary_trait["haveinfo"]:
        return {
            "status": "not-found",
            "message": f"Could not find primary trait {primary_trait['trait_fullname']}"
        }
    group = primary_trait["db"]["group"]
    primary_trait_data = all_traits_data[primary_trait["trait_name"]]
    primary_samples, primary_values, _primary_variances = export_informative(
        primary_trait_data)

    cntrl_traits = tuple(
        trait for trait in all_traits
        if trait["trait_fullname"] != primary_trait_name)
    cntrl_traits_data = tuple(
        data for trait_name, data in all_traits_data.items()
        if trait_name != primary_trait["trait_name"])
    species = species_name(conn, group)

    (cntrl_samples,
     cntrl_values,
     _cntrl_variances,
     _cntrl_ns) = control_samples(cntrl_traits_data, primary_samples)

    common_primary_control_samples = primary_samples
    fixed_primary_vals = primary_values
    fixed_control_vals = cntrl_values
    if not all(cnt_smp == primary_samples for cnt_smp in cntrl_samples):
        (common_primary_control_samples,
         fixed_primary_vals,
         fixed_control_vals,
         _primary_variances,
         _cntrl_variances) = fix_samples(primary_trait, cntrl_traits)

    if len(common_primary_control_samples) < corr_min_informative:
        return {
            "status": "error",
            "message": (
                f"Fewer than {corr_min_informative} samples data entered for "
                f"{group} dataset. No calculation of correlation has been "
                "attempted."),
            "error_type": "Inadequate Samples"}

    identical_traits_names = find_identical_traits(
        primary_trait_name, primary_values, control_trait_names, cntrl_values)
    if len(identical_traits_names) > 0:
        return {
            "status": "error",
            "message": (
                f"{identical_traits_names[0]} and {identical_traits_names[1]} "
                "have the same values for the {len(fixed_primary_vals)} "
                "samples that will be used to compute the partial correlation "
                "(common for all primary and control traits). In such cases, "
                "partial correlation cannot be computed. Please re-select your "
                "traits."),
            "error_type": "Identical Traits"}

    input_trait_geneid = primary_trait.get("geneid", 0)
    input_trait_symbol = primary_trait.get("symbol", "")
    input_trait_mouse_geneid = translate_to_mouse_gene_id(
        species, input_trait_geneid, conn)

    tissue_probeset_freeze_id = 1
    db_type = primary_trait["db"]["dataset_type"]

    if db_type == "ProbeSet" and method.lower() in (
            "sgo literature correlation",
            "tissue correlation, pearson's r",
            "tissue correlation, spearman's rho"):
        return {
            "status": "error",
            "message": (
                "Wrong correlation type: It is not possible to compute the "
                f"{method} between your trait and data in the {target_db_name} "
                "database. Please try again after selecting another type of "
                "correlation."),
            "error_type": "Correlation Type"}

    if (method.lower() == "sgo literature correlation" and (
            bool(input_trait_geneid) is False or
            check_for_literature_info(conn, input_trait_mouse_geneid))):
        return {
            "status": "error",
            "message": (
                "No Literature Information: This gene does not have any "
                "associated Literature Information."),
            "error_type": "Literature Correlation"}

    if (
            method.lower() in (
                "tissue correlation, pearson's r",
                "tissue correlation, spearman's rho")
            and bool(input_trait_symbol) is False):
        return {
            "status": "error",
            "message": (
                "No Tissue Correlation Information: This gene does not have "
                "any associated Tissue Correlation Information."),
            "error_type": "Tissue Correlation"}

    if (
            method.lower() in (
                "tissue correlation, pearson's r",
                "tissue correlation, spearman's rho")
            and check_symbol_for_tissue_correlation(
                conn, tissue_probeset_freeze_id, input_trait_symbol)):
        return {
            "status": "error",
            "message": (
                "No Tissue Correlation Information: This gene does not have "
                "any associated Tissue Correlation Information."),
            "error_type": "Tissue Correlation"}

    target_dataset = retrieve_trait_dataset(
        ("Temp" if "Temp" in target_db_name else
         ("Publish" if "Publish" in target_db_name else
          "Geno" if "Geno" in target_db_name else "ProbeSet")),
        {"db": {"dataset_name": target_db_name}, "trait_name": "_"},
        threshold,
        conn)

    database_filename = get_filename(conn, target_db_name, TEXTDIR)
    _total_traits, all_correlations = partial_corrs(
        conn, common_primary_control_samples, fixed_primary_vals,
        fixed_control_vals, len(fixed_primary_vals), species,
        input_trait_geneid, input_trait_symbol, tissue_probeset_freeze_id,
        method, {**target_dataset, "dataset_type": target_dataset["type"]}, database_filename)


    def __make_sorter__(method):
        def __by_lit_or_tiss_corr_then_p_val__(row):
            return (row[6], row[3])

        def __by_partial_corr_p_value__(row):
            return row[3]

        if (("literature" in method.lower()) or ("tissue" in method.lower())):
            return __by_lit_or_tiss_corr_then_p_val__

        return __by_partial_corr_p_value__

    add_lit_corr_and_tiss_corr = compose(
        partial(literature_correlation_by_list, conn, species),
        partial(
            tissue_correlation_by_list, conn, input_trait_symbol,
            tissue_probeset_freeze_id, method))

    selected_results = sorted(
        all_correlations,
        key=__make_sorter__(method))[:criteria]
    traits_list_corr_info = {
        f"{target_dataset['dataset_name']}::{item[0]}": {
            "noverlap": item[1],
            "partial_corr": item[2],
            "partial_corr_p_value": item[3],
            "corr": item[4],
            "corr_p_value": item[5],
            "rank_order": (1 if "spearman" in method.lower() else 0),
            **({
                "tissue_corr": item[6],
                "tissue_p_value": item[7]}
               if len(item) == 8 else {}),
            **({"l_corr": item[6]}
               if len(item) == 7 else {})
        } for item in selected_results}

    trait_list = add_lit_corr_and_tiss_corr(tuple(
        {**trait, **traits_list_corr_info.get(trait["trait_fullname"], {})}
        for trait in traits_info(
            conn, threshold,
            tuple(
                f"{target_dataset['dataset_name']}::{item[0]}"
                for item in selected_results))))

    return {
        "status": "success",
        "results": {
            "primary_trait": trait_for_output(primary_trait),
            "control_traits": tuple(
                trait_for_output(trait) for trait in cntrl_traits),
            "correlations": tuple(
                trait_for_output(trait) for trait in trait_list),
            "dataset_type": target_dataset["type"],
            "method": "spearman" if "spearman" in method.lower() else "pearson"
        }}
