"""module contains code for doing correlation"""

import json
import collections
from gn3.base.data_set import create_dataset
from gn3.utility.helper_functions import get_species_dataset_trait
from gn3.utility.corr_result_helpers import normalize_values
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

        sample_val_dict = json.loads(start_vars["sample_vals"])

        for sample in sample_names:
            if sample not in excluded_samples:
                value = sample_val_dict[sample]

                if not value.strip().lower() == "x":
                    self.sample_data[str(sample)] = float(value)

    def get_sample_r_and_p_values(self, trait, target_samples):
        """Calculates the sample r (or rho) and p-value

        Given a primary trait and a target trait's sample values,
        calculates either the pearson r or spearman rho and the p-value
        using the corresponding scipy functions.

        """
        self.this_trait_vals = []
        target_vals = []

        for index, sample in enumerate(self.target_dataset.samplelist):
            if sample in self.sample_data:
                sample_value = self.sample_data[sample]
                target_sample_value = target_samples[index]
                self.this_trait_vals.append(sample_value)

        self.this_trait_vals, target_vals, num_overlap = normalize_values(
            self.this_trait_vals, target_vals)

        if num_overlap > 5:
            # ZS: 2015 could add biweight correlation, see http://www.ncbi.nlm.nih.gov/pmc/articles/PMC3465711/
            if self.corr_method == 'bicor':
                sample_r, sample_p = do_bicor(
                    self.this_trait_vals, target_vals)

            elif self.corr_method == 'pearson':
                sample_r, sample_p = scipy.stats.pearsonr(
                    self.this_trait_vals, target_vals)

            else:
                sample_r, sample_p = scipy.stats.spearmanr(
                    self.this_trait_vals, target_vals)

            if numpy.isnan(sample_r):
                pass

            else:

                self.correlation_data[trait] = [
                    sample_r, sample_p, num_overlap]

    def do_correlation(self, start_vars):

        # print(start_vars)

        # should probably rename this method cause all that happens is variabe assignment and

        # start_vars = self.start_vars
        if start_vars["dataset"] == "Temp":
            self.dataset = create_dataset(
                dataset_name="Temp", dataset_type="Temp", group_name=start_vars['group'])

            self.trait_id = start_vars['trait_id']

            # should pass as argument

            # current issue is that self.dataset.group.sampelist returns None

            self.this_trait = create_trait(dataset=self.dataset,
                                           name=self.trait_id,
                                           cellid=None)

        else:

            # should the function as an argument

            get_species_dataset_trait(self, start_vars)

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
            self.location_type = str(start_vars['location_type'])
            self.location_chr = str(start_vars['loc_chr'])

            try:
                self.min_location_mb = int(start_vars['min_loc_mb'])
                self.max_location_mb = int(start_vars['max_loc_mb'])
            except Exception as e:
                self.min_location_mb = None
                self.max_location_mb = None

        else:
            self.location_type = self.location_chr = self.min_location_mb = self.max_location_mb = None

        self.get_formatted_corr_type()

        self.return_number = int(start_vars['corr_return_results'])

        print("EEEEEEEEEEEEEEEEE", self.dataset.group.samplelist)
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

        self.target_dataset = create_dataset(start_vars['corr_dataset'])

        # whe the code below self.target_dataset was added things get very slow should fix this

        self.target_dataset.get_trait_data(list(self.sample_data.keys()))

        self.header_fields = get_header_fields(
            self.target_dataset.type, self.corr_method)

        if self.target_dataset.type == "ProbeSet":
            self.filter_cols = [7, 6]

        elif self.target_dataset.type == "Publish":
            self.filter_cols = [6, 0]

        else:
            self.filter_cols = [4, 0]

        self.correlation_results = []

        self.correlation_data = {}

        # furst try sample type
        if self.corr_type == "sample":
            for trait, values in list(self.target_dataset.trait_data.items()):
                # print(trait,values)
                self.get_sample_r_and_p_values(trait, values)

        self.correlation_data = collections.OrderedDict(sorted(list(self.correlation_data.items()),
                                                               key=lambda t: -abs(t[1][0])))


        #ZS: Convert min/max chromosome to an int for the location range option

        range_chr_as_int = None
        for order_id, chr_info in list(self.dataset.species.chromosomes.chromosomes.items()):
            if 'loc_chr' in start_vars:
                if chr_info.name == self.location_chr:
                    range_chr_as_int = order_id

            print(chr_info,order_id)


        # should return json data after computing correlation

        # return self

        return {
            "group": self.dataset.group,
            "target_dataset": self.target_dataset.group,
            "header_fields": self.header_fields,
            "correlation_data": self.correlation_data,
            "trait_values": self.this_trait_vals
        }


def get_header_fields(data_type, corr_method):
    if data_type == "ProbeSet":
        if corr_method == "spearman":

            header_fields = ['Index',
                             'Record',
                             'Symbol',
                             'Description',
                             'Location',
                             'Mean',
                             'Sample rho',
                             'N',
                             'Sample p(rho)',
                             'Lit rho',
                             'Tissue rho',
                             'Tissue p(rho)',
                             'Max LRS',
                             'Max LRS Location',
                             'Additive Effect']

        else:
            header_fields = ['Index',
                             'Record',
                             'Abbreviation',
                             'Description',
                             'Mean',
                             'Authors',
                             'Year',
                             'Sample r',
                             'N',
                             'Sample p(r)',
                             'Max LRS',
                             'Max LRS Location',
                             'Additive Effect']

    elif data_type == "Publish":
        if corr_method == "spearman":

            header_fields = ['Index',
                             'Record',
                             'Abbreviation',
                             'Description',
                             'Mean',
                             'Authors',
                             'Year',
                             'Sample rho',
                             'N',
                             'Sample p(rho)',
                             'Max LRS',
                             'Max LRS Location',
                             'Additive Effect']

        else:
            header_fields = ['Index',
                             'Record',
                             'Abbreviation',
                             'Description',
                             'Mean',
                             'Authors',
                             'Year',
                             'Sample r',
                             'N',
                             'Sample p(r)',
                             'Max LRS',
                             'Max LRS Location',
                             'Additive Effect']

    else:
        if corr_method == "spearman":
            header_fields = ['Index',
                             'ID',
                             'Location',
                             'Sample rho',
                             'N',
                             'Sample p(rho)']

        else:
            header_fields = ['Index',
                             'ID',
                             'Location',
                             'Sample r',
                             'N',
                             'Sample p(r)']

    return header_fields
