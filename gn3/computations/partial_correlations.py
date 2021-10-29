"""
This module deals with partial correlations.

It is an attempt to migrate over the partial correlations feature from
GeneNetwork1.
"""

from functools import reduce
from typing import Any, Tuple, Sequence

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
    return tuple(
        {
            sample: {"sample_name": sample, "value": val, "variance": var}
            for sample, val, var in zip(*trait_line)
        } for trait_line in zip(*(samples_vals_vars[0:3])))

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
        ckey = "{:.3f}".format(control_item[0])
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

def batch_computed_tissue_correlation(
        trait_value: str, symbol_value_dict: dict,
        method: str = "pearson") -> Tuple[dict, dict]:
    """
    `web.webqtl.correlation.correlationFunction.batchCalTissueCorr`"""
    raise Exception("Not implemented!")
    return ({}, {})
