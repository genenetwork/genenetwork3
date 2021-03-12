"""module contains code for any computation in correlation"""

import json
from .show_corr_results import CorrelationResults

def compute_correlation(correlation_input_data,
                        correlation_results=CorrelationResults):
    """function that does correlation .creates Correlation results instance

    correlation_input_data structure is a dict with

     {
     "trait_id":"valid trait id",
     "dataset":"",
      "sample_vals":{},
      "primary_samples":"",
      "corr_type":"",
      corr_dataset:"",
      "corr_return_results":"",

       
     }

    """

    corr_object = correlation_results(
        start_vars=correlation_input_data)

    corr_results = corr_object.do_correlation(start_vars=correlation_input_data)
    # possibility of file being so large cause of the not sure whether to return a file

    return corr_results
