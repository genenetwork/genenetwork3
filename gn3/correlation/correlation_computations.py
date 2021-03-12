"""module contains code for any computation in correlation"""

import json
from .show_corr_results import CorrelationResults


def filter_wanted_inputs():
    """todo:split the get loading page data function"""
    raise NotImplementedError()


# def filter_input_data(initial_start_vars):
#     """functional to filter form/json data and create_dataset and trait"""
#     if initial_start_vars is None:
#         # added this just to enable testing of this function
#         raise NotImplementedError()

#     start_vars_container = {}
#     n_samples = 0
#     if "wanted_inputs" in initial_start_vars:
#         wanted = initial_start_vars["wanted_inputs"].split(",")
#         start_vars = {}

#         for key, value in initial_start_vars.items():
#             if key in wanted:
#                 start_vars[key] = value

#         # if "n_samples" in start_vars:
#         #     n_samples = int(start_vars["n_samples"])

#         # else:
#         #     sample_vals_dict = json.loads(start_vars['sample_vals'])
#         #     samples = start_vars['primary_samples'].split(",")

#         #     for sample in samples:
#         #         if sample in sample_vals_dict:
#         #             if sample_vals_dict[sample] != "x":
#         #                 n_samples += 1

#         # start_vars['n_samples'] = n_samples
#         start_vars['wanted_inputs'] = initial_start_vars['wanted_inputs']

#         start_vars_container['start_vars'] = start_vars

#     else:

#         start_vars_container['start_vars'] = initial_start_vars

#     return start_vars_container


def compute_correlation(correlation_input_data,
                        correlation_results=CorrelationResults):
    """function that does correlation .creates Correlation results instance"""

    # start_vars_container = get_input_data(
    #     initial_start_vars=init_start_vars)

    # start_vars = start_vars_container["start_vars"]

    corr_object = correlation_results(
        start_vars=correlation_input_data)

    corr_results = corr_object.do_correlation(start_vars=correlation_input_data)
    # possibility of file being so large cause of the not sure whether to return a file

    return corr_results
