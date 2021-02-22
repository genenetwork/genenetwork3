"""module contains utility functions for correlation"""


class AttributeSetter:
    def __init__(self, trait_obj):
        for key, value in trait_obj.items():
            setattr(self, key, value)


def create_dataset(dataset_name, dataset_type, group_name):
    """mock function for creating dataset"""

    dataset = AttributeSetter({
        "group": AttributeSetter({
            "genofile": "",
            "samplelist": "S1",
            "parlist": "",
            "f1list": ""


        })
    })

    return dataset


def create_trait(dataset, name, cellid):
    """mock function for creating trait"""

    trait = AttributeSetter({
        "group": AttributeSetter({
            "genofile": ""
        })
    })

    return trait


def get_species_dataset_trait(self_obj, start_vars):
    # do somethig return
    """function should somehow mutate the passed object"""

    return ""


def get_genofile_samplelist(dataset):
    return ["C57BL/6J"]
