"""module contains code for doing correlation"""

import json

from gn3.base.data_set  import create_dataset
from gn3.utility.helper_functions import get_species_dataset_trait
# from .correlation_utility import create_dataset
# from .correlation_utility import create_trait
from gn3.base.trait import create_trait
# from .correlation_utility import get_species_dataset_trait


class CorrelationResults:
    def __init__(self, start_vars):
        self.assertion_for_start_vars(start_vars)
        # if no assertion error is raised do

    @staticmethod
    def assertion_for_start_vars(start_vars):

        # should better ways to assert the variables
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

    def get_formatted_corr_type(self):
        self.formatted_corr_type = ""
        if self.corr_type == "lit":
            self.formatted_corr_type += "Literature Correlation "
        elif self.corr_type == "tissue":
            self.formatted_corr_type += "Tissue Correlation "
        elif self.corr_type == "sample":
            self.formatted_corr_type += "Genetic Correlation "

        if self.corr_method == "pearson":
            self.formatted_corr_type += "(Pearson's r)"
        elif self.corr_method == "spearman":
            self.formatted_corr_type += "(Spearman's rho)"
        elif self.corr_method == "bicor":
            self.formatted_corr_type += "(Biweight r)"

    def process_samples(self, start_vars, sample_names, excluded_samples=None):
        if not excluded_samples:
            excluded_samples = ()

        return

        # currently the below code fails as sample_vals is not passed

        sample_val_dict = json.loads(start_vars['sample_vals'])
        for sample in sample_names:
            pass

    def do_correlation(self, start_vars):

        # print(start_vars)

        # should probably rename this method cause all that happens is variabe assignment and

        # start_vars = self.start_vars
        if start_vars["dataset"] == "Temp":
            self.dataset = create_dataset(
                dataset_name="Temp", dataset_type="Temp", group_name=start_vars['group'])

            self.trait_id = start_vars['trait_id']

            # should pass as argument

            self.this_trait = create_trait(dataset=self.dataset,
                                           name=self.trait_id,
                                           cellid=None)

        else:

            # should the function as an argument

            get_species_dataset_trait(self, start_vars)

        print("UUUUUUUUUUUUUUUUUUUUUu",self.dataset.group.name)

        corr_samples_group = start_vars['corr_samples_group']
        # corr_samples_group = 

        self.sample_data = {}

        self.corr_type = start_vars["corr_type"]

        self.corr_method = start_vars['corr_sample_method']

        # try to use a function to check for types to cannot be coerced to specified types

        self.min_expr = float(
            start_vars["min_expr"]) if start_vars["min_expr"] != "" else None

        self.p_range_lower = float(
            start_vars["p_range_lower"]) if start_vars["p_range_lower"] != "" else None

        self.p_range_upper = float(
            start_vars["p_range_upper"]) if start_vars["p_range_upper"] != "" else None

        if ("loc_chr" in start_vars and "min_loc_mb" in start_vars and "max_loc_mb" in start_vars):
            self.location_type = string(start_vars['location_type'])
            self.location_chr = string(start_vars['loc_chr'])
            self.min_location_mb = int(start_vars['min_loc_mb'])
            self.max_location_mb = int(start_vars['max_loc_mb'])

        else:
            self.location_type = self.location_chr = self.min_location_mb = self.max_location_mb = None

        self.get_formatted_corr_type()

        self.return_number = int(start_vars['corr_return_results'])
        primary_samples = self.dataset.group.samplelist

        # The two if statements below append samples to the sample list based upon whether the user
        # rselected Primary Samples Only, Other Samples Only, or All Samples

        if self.dataset.group.parlist != None:
            primary_samples += self.dataset.group.parlist

        if self.dataset.group.f1list != None:
            primary_samples += self.dataset.group.f1list

        # If either BXD/whatever Only or All Samples, append all of that group's samplelist

        if corr_samples_group != 'samples_other':
            # currently doing nothing
            self.process_samples(start_vars, primary_samples)

        if corr_samples_group != 'samples_primary':
            if corr_samples_group == 'samples_other':
                primary_samples = [x for x in primary_samples if x not in (
                    self.dataset.group.parlist + self.dataset.group.f1list)]

             # currently doing nothing
            self.process_samples(start_vars, list(
                self.this_trait.data.keys()), primary_samples)

        # should return json data after computing correlation

        return {
          "hello":"hey"
        }
