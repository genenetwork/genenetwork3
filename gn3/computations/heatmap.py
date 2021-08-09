"""
This module will contain functions to be used in computation of the data used to
generate various kinds of heatmaps.
"""

from gn3.computations.slink import slink
from gn3.computations.correlations2 import compute_correlation

def export_trait_data(
        trait_data: dict, strainlist: Sequence[str], dtype: str="val",
        var_exists: bool=False, n_exists: bool=False):
    """
    Export data according to `strainlist`. Mostly used in calculating
    correlations.

    DESCRIPTION:
    Migrated from
    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/base/webqtlTrait.py#L166-L211

    PARAMETERS
    trait: (dict)
      The dictionary of key-value pairs representing a trait
    strainlist: (list)
      A list of strain names
    type: (str)
      ... verify what this is ...
    var_exists: (bool)
      A flag indicating existence of variance
    n_exists: (bool)
      A flag indicating existence of ndata
    """
    def __export_all_types(tdata, strain):
        sample_data = []
        if tdata[strain]["val"]:
            sample_data.append(tdata[strain]["val"])
            if var_exists:
                if tdata[strain].var:
                    sample_data.append(tdata[strain]["var"])
                else:
                    sample_data.append(None)
            if n_exists:
                if tdata[strain]["ndata"]:
                    sample_data.append(tdata[strain]["ndata"])
                else:
                    sample_data.append(None)
        else:
            if var_exists and n_exists:
                sample_data += [None, None, None]
            elif var_exists or n_exists:
                sample_data += [None, None]
            else:
                sample_data.append(None)

        return tuple(sample_data)

    def __exporter(accumulator, strain):
        if tdata.has_key(strain):
            if dtype == "val":
                return accumulator + (tdata[strain]["val"], )
            if dtype == "var":
                return accumulator + (tdata[strain]["var"], )
            if dtype == "N":
                return tdata[strain]["ndata"]
            if dtype == "all":
                return accumulator + __export_all_types(
                    accumulator, tdata, strain)
            else:
                raise KeyError("Type `%s` is incorrect" % dtype)
        else:
            if var_exists and n_exists:
                return accumulator + (None, None, None)
            if var_exists or n_exists:
                return accumulator + (None, None)
            return accumulator + (None,)

    return reduce(__exporter(strain), strainlist, tuple())

def trait_display_name(trait: Dict):
    """
    Given a trait, return a name to use to display the trait on a heatmap.

    DESCRIPTION
    Migrated from
    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/base/webqtlTrait.py#L141-L157
    """
    if trait.get("db", None) and trait.get("trait_name", None):
        if trait["db"]["dataset_type"] == "Temp":
            desc = trait["description"]
            if desc.find("PCA") >= 0:
                return "%s::%s" % (
                    trait["db"]["displayname"],
                    desc[desc.rindex(':')+1:].strip())
            return "%s::%s" % (
                trait["db"]["displayname"],
                desc[:desc.index('entered')].strip())
        else:
            prefix = "%s::%s" % (
                trait["db"]["dataset_name"], trait["trait_name"])
            if trait["cellid"]:
                return "%s::%s" % (prefix, trait["cellid"])
            return prefix
    return trait["description"]

def cluster_traits(traits_data_list: Sequence[Dict]):
    """
    Clusters the trait values.

    DESCRIPTION
    Attempts to replicate the clustering of the traits, as done at
    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/heatmap/Heatmap.py#L138-L162
    """
    def __compute_corr(tdata_i, tdata_j):
        if tdata_j[0] < tdata_i[0]:
            corr, nOverlap = compute_correlation(tdata_i, tdata_j)
            if (1 - corr) < 0:
                return 0.0
            return 1 - corr
        return 0.0

    def __cluster(tdata_i):
        res2 = tuple(
            __compute_corr(tdata_i, tdata_j) for tdata_j in enumerate(traits))

    return tuple(__cluster(tdata_i) for tdata_i in enumerate(traits_data_list))

def heatmap_data(
        fd, search_result, conn: Any, colorScheme=None, userPrivilege=None,
        userName=None):
    """
    heatmap function

    DESCRIPTION
    This function is an attempt to reproduce the initialisation at
    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/heatmap/Heatmap.py#L46-L64
    and also the clustering and slink computations at
    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/heatmap/Heatmap.py#L138-L165
    with the help of the `gn3.computations.heatmap.cluster_traits` function.

    It does not try to actually draw the heatmap image.

    PARAMETERS:
    TODO: Elaborate on the parameters here...
    """
    cluster_checked = fd.formdata.getvalue("clusterCheck", "")
    strainlist = [strain for strain in fd.strainlist if strain not in fd.parlist]
    genotype = fd.genotype

    def __retrieve_traitlist_and_datalist(threshold, fullname):
        trait = retrieve_trait_info(threshold, fullname, conn)
        return (trait, export_trait_data(retrieve_trait_data(trait), strainlist))

    traits_details = [
        __retrieve_traitlist_and_datalist(threshold, fullname)
        for fullname in search_result]
    traits_list = map(lambda x: x[0], traits_details)
    traits_data_list = map(lambda x: x[1], traits_details)

    return {
        "target_description_checked": fd.formdata.getvalue(
            "targetDescriptionCheck", ""),
        "cluster_checked": cluster_checked,
        "slink_data": (
            slink(cluster_traits(traits_list, strainlist))
            if cluster_checked else False)
        "sessionfile": fd.formdata.getvalue("session"),
        "genotype": genotype,
        "nLoci": sum(map(lambda x: len(x), genotype))
        "strainlist": strainlist,
        "ppolar": fd.ppolar,
        "mpolar":fd.mpolar,
        "traits_list": traits_list
        "traits_data_list": traits_data_list
    }
