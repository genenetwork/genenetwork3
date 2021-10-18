"""
This module deals with partial correlations.

It is an attempt to migrate over the partial correlations feature from
GeneNetwork1.
"""

from functools import reduce

def export_informative(trait_data: dict, inc_var: bool = False) -> tuple:
    """
    Export informative strain

    This is a migration of the `exportInformative` function in
    web/webqtl/base/webqtlTrait.py module in GeneNetwork1.

    There is a chance that the original implementation has a bug, especially
    dealing with the `inc_var` value. It the `inc_var` value is meant to control
    the inclusion of the `variance` value, then the current implementation, and
    that one in GN1 have a bug.
    """
    def __exporter__(acc, data_item):
        if not inc_var or data_item["variance"] is not None:
            return (
                acc[0] + (data_item["sample_name"],),
                acc[1] + (data_item["value"],),
                acc[2] + (data_item["variance"],))
        return acc
    return reduce(
        __exporter__,
        filter(lambda td: td["value"] is not None, trait_data["data"].values()),
        (tuple(), tuple(), tuple()))
