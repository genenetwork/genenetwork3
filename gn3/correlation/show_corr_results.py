"""module contains code for doing correlation"""


def create_dataset(dataset_name, dataset_type, group_name):
    """mock function for creating dataset"""

    dataset = AttributeSetter({
        "group": AttributeSetter({
            "genofile": ""
        })
    })

    return dataset


def create_trait(dataset, name, cellid):
    """mock function for creating dataset"""

    trait = AttributeSetter({
        "group": AttributeSetter({
            "genofile": ""
        })
    })

    return trait


def get_species_dataset(self_obj, start_vars):
    # do somethig return
    """function should somehow mutate the passed object"""

    return ""


class AttributeSetter:
    def __init__(self, trait_obj):
        for key, value in trait_obj.items():
            setattr(self, key, value)


class CorrelationResults:
    def __init__(self, start_vars):
        self.assertion_for_start_vars(start_vars)
        # if no assertion error is raised do

    @staticmethod
    def assertion_for_start_vars(start_vars):

        #should better ways to assert the variables
        # example includes sample
        assert("corr_type" in start_vars)
        assert(isinstance(start_vars['corr_type'], str))
        # example includes pearson
        assert('corr_sample_method' in start_vars)
        assert('corr_dataset' in start_vars)
        # means the  limit
        assert('corr_return_results' in start_vars)

        if "loc_chr" in start_vars:
            assert('min_loc_mb' in start_vars)
            assert('max_loc_mb' in start_vars)

    def do_correlation(self, start_vars):

        # start_vars = self.start_vars
        if start_vars["dataset"] == "Temp":
            self.dataset = create_dataset(
                dataset_name="Temp", dataset_type="Temp", group_name=start_vars['group'])

            self.trait_id = start_vars['trait_id']

            self.this_trait = create_trait(dataset=self.dataset,
                                           name=self.trait_id,
                                           cellid=None)

        else:

            get_species_dataset_trait(self, start_vars)


        return self.__dict__

