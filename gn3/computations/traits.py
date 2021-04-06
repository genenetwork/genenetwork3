"""module contains all operating related to traits"""
from gn3.computations.datasets import retrieve_trait_sample_data


def fetch_trait(dataset, trait_name: str, database) -> dict:
    """this method creates a trait by\
    fetching required data given the\
    dataset and trait_name"""

    created_trait = {
        "dataset": dataset,
        "trait_name": trait_name
    }

    trait_data = get_trait_sample_data(dataset, trait_name, database)

    created_trait["trait_data"] = trait_data

    return created_trait


def get_trait_sample_data(trait_dataset, trait_name, database) -> dict:
    """first try to fetch the traits sample data from redis if that\
    try to fetch from the traits dataset redis is only  used for\
    temp dataset type which is not used in this case """

    sample_results = retrieve_trait_sample_data(
        trait_dataset, trait_name, database)

    trait_data = {}

    for (name, sample_value, _variance, _numcase, _name2) in sample_results:

        trait_data[name] = sample_value
    return trait_data


def get_trait_info_data(trait_dataset,
                        trait_name: str,
                        database_instance,
                        get_qtl_info: bool = False) -> dict:
    """given a dataset and trait_name return a dict containing all info\
    regarding the get trait"""

    _temp_var_holder = (trait_dataset, trait_name,
                        database_instance, get_qtl_info)
    trait_info_data = {
        "description": "",
        "chr": "",
        "locus": "",
        "mb": "",
        "abbreviation": "",
        "trait_display_name": ""

    }
    return trait_info_data
