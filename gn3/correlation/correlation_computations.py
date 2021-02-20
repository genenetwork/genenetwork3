"""module contains code for any computation in correlation"""

import json



def get_loading_page_data(initial_start_vars, create_dataset, get_genofile_samplelist):
    if initial_start_vars is None:
        # added this just to enable testing
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
