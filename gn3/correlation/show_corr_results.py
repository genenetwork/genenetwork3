"""module contains code for doing correlation"""

import json
import collections
from gn3.base.data_set import create_dataset
from gn3.utility.helper_functions import get_species_dataset_trait
from gn3.utility.corr_result_helpers import normalize_values
from gn3.base.trait import create_trait


class CorrelationResults:
    def __init__(self, start_vars):
        self.assertion_for_start_vars(start_vars)

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

            self.this_trait = create_trait(dataset=self.dataset,
                                           name=self.trait_id,
                                           cellid=None)

        else:

            # should the function as an argument

            get_species_dataset_trait(self, start_vars)

        corr_samples_group = start_vars['corr_samples_group']
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

                # the code is below is basically a temporary fix
                self.min_location_mb = int(start_vars['min_loc_mb'])
                self.max_location_mb = int(start_vars['max_loc_mb'])
            except Exception as e:
                self.min_location_mb = None
                self.max_location_mb = None

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

        self.target_dataset = create_dataset(start_vars['corr_dataset'])

        # whe the code below ie getting trait data was added things get very slow should fix this

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

        # first try sample type
        if self.corr_type == "sample":
            for trait, values in list(self.target_dataset.trait_data.items()):
                # print(trait,values)
                self.get_sample_r_and_p_values(trait, values)

        self.correlation_data = collections.OrderedDict(sorted(list(self.correlation_data.items()),
                                                               key=lambda t: -abs(t[1][0])))

        # ZS: Convert min/max chromosome to an int for the location range option

        range_chr_as_int = None
        for order_id, chr_info in list(self.dataset.species.chromosomes.chromosomes.items()):
            if 'loc_chr' in start_vars:
                if chr_info.name == self.location_chr:
                    range_chr_as_int = order_id

        # not sure what happens in this for loop
        for _trait_counter, trait in enumerate(list(self.correlation_data.keys())[:self.return_number]):
            trait_object = create_trait(
                dataset=self.target_dataset, name=trait, get_qtl_info=True, get_sample_info=False)
            if not trait_object:
                print("trait object is empty")
                continue

            chr_as_int = 0
            # also not sure why we have the same loop
            for order_id, chr_info in list(self.dataset.species.chromosomes.chromosomes.items()):
                if self.location_type == "highest_lod":
                    if chr_info.name == trait_object.locus_chr:
                        chr_as_int = order_id

                else:
                    if chr_info.name == trait_object.chr:
                        chr_as_int = order_id

            if (float(self.correlation_data[trait][0]) >= self.p_range_lower and
                    float(self.correlation_data[trait][0]) <= self.p_range_upper):
                print("working on this")

                if (self.target_dataset.type == "ProbeSet" or self.target_dataset.type == "Publish") and bool(trait_object.mean):
                    if (self.min_expr != None) and (float(trait_object.mean) < self.min_expr):
                        continue

                if range_chr_as_int != None and (chr_as_int != range_chr_as_int):
                    continue
                if self.location_type == "highest_lod":
                    if (self.min_location_mb != None) and (float(trait_object.locus_mb) < float(self.min_location_mb)):
                        continue
                    if (self.max_location_mb != None) and (float(trait_object.locus_mb) > float(self.max_location_mb)):
                        continue
                else:
                    if (self.min_location_mb != None) and (float(trait_object.mb) < float(self.min_location_mb)):
                        continue
                    if (self.max_location_mb != None) and (float(trait_object.mb) > float(self.max_location_mb)):
                        continue

                (trait_object.sample_r,
                 trait_object.sample_p,
                 trait_object.num_overlap) = self.correlation_data[trait]

                # Set some sane defaults
                trait_object.tissue_corr = 0
                trait_object.tissue_pvalue = 0
                trait_object.lit_corr = 0
                if self.corr_type == "tissue" and tissue_corr_data != None:
                    trait_object.tissue_corr = tissue_corr_data[trait][1]
                    trait_object.tissue_pvalue = tissue_corr_data[trait][2]
                elif self.corr_type == "lit":
                    trait_object.lit_corr = lit_corr_data[trait][1]

                self.correlation_results.append(trait_object)

            if self.corr_type != "lit" and self.dataset.type == "ProbeSet" and self.target_dataset.type == "ProbeSet":
                self.do_lit_correlation_for_trait_list()

            if self.corr_type != "tissue" and self.dataset.type == "ProbeSet" and self.target_dataset.type == "ProbeSet":
                self.do_tissue_correlation_for_trait_list()

        self.json_results = generate_corr_json(
            self.correlation_results, self.this_trait, self.dataset, self.target_dataset)

        return {
            "group": self.dataset.group,
            "target_dataset": self.target_dataset.group,
            "header_fields": self.header_fields,
            "correlation_data": self.correlation_data,
            "trait_values": self.this_trait_vals,
            "json_results": self.json_results
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


def generate_corr_json(corr_results, this_trait, dataset, target_dataset, for_api=False):
    results_list = []
    for i, trait in enumerate(corr_results):
        if trait.view == False:
            continue
        results_dict = {}
        results_dict['index'] = i + 1
        results_dict['trait_id'] = trait.name
        results_dict['dataset'] = trait.dataset.name
        results_dict['hmac'] = hmac.data_hmac(
            '{}:{}'.format(trait.name, trait.dataset.name))
        if target_dataset.type == "ProbeSet":
            results_dict['symbol'] = trait.symbol
            results_dict['description'] = "N/A"
            results_dict['location'] = trait.location_repr
            results_dict['mean'] = "N/A"
            results_dict['additive'] = "N/A"
            if bool(trait.description_display):
                results_dict['description'] = trait.description_display
            if bool(trait.mean):
                results_dict['mean'] = f"{float(trait.mean):.3f}"
            try:
                results_dict['lod_score'] = f"{float(trait.LRS_score_repr) / 4.61:.1f}"
            except:
                results_dict['lod_score'] = "N/A"
            results_dict['lrs_location'] = trait.LRS_location_repr
            if bool(trait.additive):
                results_dict['additive'] = f"{float(trait.additive):.3f}"
            results_dict['sample_r'] = f"{float(trait.sample_r):.3f}"
            results_dict['num_overlap'] = trait.num_overlap
            results_dict['sample_p'] = f"{float(trait.sample_p):.3e}"
            results_dict['lit_corr'] = "--"
            results_dict['tissue_corr'] = "--"
            results_dict['tissue_pvalue'] = "--"
            if bool(trait.lit_corr):
                results_dict['lit_corr'] = f"{float(trait.lit_corr):.3f}"
            if bool(trait.tissue_corr):
                results_dict['tissue_corr'] = f"{float(trait.tissue_corr):.3f}"
                results_dict['tissue_pvalue'] = f"{float(trait.tissue_pvalue):.3e}"
        elif target_dataset.type == "Publish":
            results_dict['abbreviation_display'] = "N/A"
            results_dict['description'] = "N/A"
            results_dict['mean'] = "N/A"
            results_dict['authors_display'] = "N/A"
            results_dict['additive'] = "N/A"
            if for_api:
                results_dict['pubmed_id'] = "N/A"
                results_dict['year'] = "N/A"
            else:
                results_dict['pubmed_link'] = "N/A"
                results_dict['pubmed_text'] = "N/A"

            if bool(trait.abbreviation):
                results_dict['abbreviation_display'] = trait.abbreviation
            if bool(trait.description_display):
                results_dict['description'] = trait.description_display
            if bool(trait.mean):
                results_dict['mean'] = f"{float(trait.mean):.3f}"
            if bool(trait.authors):
                authors_list = trait.authors.split(',')
                if len(authors_list) > 6:
                    results_dict['authors_display'] = ", ".join(
                        authors_list[:6]) + ", et al."
                else:
                    results_dict['authors_display'] = trait.authors
            if bool(trait.pubmed_id):
                if for_api:
                    results_dict['pubmed_id'] = trait.pubmed_id
                    results_dict['year'] = trait.pubmed_text
                else:
                    results_dict['pubmed_link'] = trait.pubmed_link
                    results_dict['pubmed_text'] = trait.pubmed_text
            try:
                results_dict['lod_score'] = f"{float(trait.LRS_score_repr) / 4.61:.1f}"
            except:
                results_dict['lod_score'] = "N/A"
            results_dict['lrs_location'] = trait.LRS_location_repr
            if bool(trait.additive):
                results_dict['additive'] = f"{float(trait.additive):.3f}"
            results_dict['sample_r'] = f"{float(trait.sample_r):.3f}"
            results_dict['num_overlap'] = trait.num_overlap
            results_dict['sample_p'] = f"{float(trait.sample_p):.3e}"
        else:
            results_dict['location'] = trait.location_repr
            results_dict['sample_r'] = f"{float(trait.sample_r):.3f}"
            results_dict['num_overlap'] = trait.num_overlap
            results_dict['sample_p'] = f"{float(trait.sample_p):.3e}"

        results_list.append(results_dict)

    return json.dumps(results_list)
