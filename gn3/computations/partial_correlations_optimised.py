"""
This contains an optimised version of the
 `gn3.computations.partial_correlations.partial_correlations_entry`
function.
"""
from functools import partial
from typing import Any, Tuple

from gn3.settings import TEXTDIR
from gn3.function_helpers import  compose
from gn3.db.partial_correlations import traits_info, traits_data
from gn3.db.species import species_name, translate_to_mouse_gene_id
from gn3.db.traits import export_informative, retrieve_trait_dataset
from gn3.db.correlations import (
    get_filename,
    check_for_literature_info,
    check_symbol_for_tissue_correlation)
from gn3.computations.partial_correlations import (
    fix_samples,
    partial_corrs,
    control_samples,
    trait_for_output,
    find_identical_traits,
    tissue_correlation_by_list,
    literature_correlation_by_list)

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

    # primary_trait = retrieve_trait_info(threshold, primary_trait_name, conn)
    primary_trait = tuple(
        trait for trait in all_traits
        if trait["trait_fullname"] == primary_trait_name)[0]
    group = primary_trait["db"]["group"]
    # primary_trait_data = retrieve_trait_data(primary_trait, conn)
    primary_trait_data = all_traits_data[primary_trait["trait_name"]]
    primary_samples, primary_values, _primary_variances = export_informative(
        primary_trait_data)

    # cntrl_traits = tuple(
    #     retrieve_trait_info(threshold, trait_full_name, conn)
    #     for trait_full_name in control_trait_names)
    # cntrl_traits_data = tuple(
    #     retrieve_trait_data(cntrl_trait, conn)
    #     for cntrl_trait in cntrl_traits)
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
        def __sort_6__(row):
            return row[6]

        def __sort_3__(row):
            return row[3]

        if "literature" in method.lower():
            return __sort_6__

        if "tissue" in method.lower():
            return __sort_6__

        return __sort_3__

    # sorted_correlations = sorted(
    #     all_correlations, key=__make_sorter__(method))

    add_lit_corr_and_tiss_corr = compose(
        partial(literature_correlation_by_list, conn, species),
        partial(
            tissue_correlation_by_list, conn, input_trait_symbol,
            tissue_probeset_freeze_id, method))

    selected_results = sorted(
        all_correlations,
        key=__make_sorter__(method))[:min(criteria, len(all_correlations))]
    traits_list_corr_info = {
        "{target_dataset['dataset_name']}::{item[0]}": {
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
