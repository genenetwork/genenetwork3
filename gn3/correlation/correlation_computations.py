"""module contains code for any computation in correlation"""

import json
from .correlation_utility import AttributeSetter
from .correlation_utility import get_genofile_samplelist


from .show_corr_results import CorrelationResults



class AttributeSetter:
    def __init__(self, trait_obj):
        for key, value in trait_obj.items():
            setattr(self, key, value)


def create_dataset(dataset):

    dataset = AttributeSetter({
        "group": AttributeSetter({
            "genofile": ""
        })
    })

    return dataset


def filter_wanted_inputs():
    """split the get loading page data function"""
    pass


def get_loading_page_data(initial_start_vars, create_dataset=create_dataset, get_genofile_samplelist=get_genofile_samplelist):
    if initial_start_vars is None:
        # added this just to enable testing of this function
        return "no items"

    """ function to create dataset and load page data """
    start_vars_container = {}
    n_samples = 0
    if "wanted_inputs" in initial_start_vars:
        wanted = initial_start_vars["wanted_inputs"].split(",")
        start_vars = {}

        for key, value in initial_start_vars.items():
            if key in wanted:
                start_vars[key] = value

        if "n_samples" in start_vars:
            n_samples = int(start_vars["n_samples"])

        else:
            sample_vals_dict = json.loads(start_vars['sample_vals'])

            dataset = create_dataset(start_vars['dataset'], group_name=start_vars['group']
                                     ) if "group" in start_vars else create_dataset(start_vars['dataset'])
            samples = start_vars['primary_samples'].split(",")

            if 'genofile' in start_vars:
                genofile_string = start_vars['genofile']
                dataset.group.genofile = genofile_string.split(":")[0]

                genofile_samples = get_genofile_samplelist(
                    dataset)

                if len(genofile_samples) > 1:
                    samples = genofile_samples

            for sample in samples:
                if sample in sample_vals_dict:
                    if sample_vals_dict[sample] != "x":
                        n_samples += 1

        start_vars['n_samples'] = n_samples
        start_vars['wanted_inputs'] = initial_start_vars['wanted_inputs']

        start_vars_container['start_vars'] = start_vars

    else:

        start_vars_container['start_vars'] = initial_start_vars

    return start_vars_container


def compute_correlation(init_start_vars, get_loading_page_data=get_loading_page_data, CorrelationResults=CorrelationResults):
    """function that does correlation .creates Correlation results instance"""

    start_vars_container = get_loading_page_data(
        initial_start_vars=init_start_vars)

    start_vars = start_vars_container["start_vars"]

    corr_object = CorrelationResults(
        start_vars=start_vars)

    corr_results = corr_object.refactored_do_correlation(start_vars=start_vars)
    # possibility of file being so large cause of the not sure whether to return a file

    return corr_results
