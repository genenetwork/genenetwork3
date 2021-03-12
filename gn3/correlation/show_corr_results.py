"""module contains code for doing correlation"""

import json
import collections
import numpy
import scipy.stats
import rpy2.robjects as ro
from flask import g
from gn3.base.data_set import create_dataset
from gn3.utility.db_tools import escape
from gn3.utility.helper_functions import get_species_dataset_trait
from gn3.utility.corr_result_helpers import normalize_values
from gn3.base.trait import create_trait
from gn3.utility import hmac
from . import correlation_functions


class CorrelationResults:
    """class for computing correlation"""
    # pylint: disable=too-many-instance-attributes
    # pylint:disable=attribute-defined-outside-init

    def __init__(self, start_vars):
        self.assertion_for_start_vars(start_vars)

    @staticmethod
    def assertion_for_start_vars(start_vars):
        # pylint: disable = E, W, R, C

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
        """method to formatt corr_types"""
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
        """method to process samples"""


        if not excluded_samples:
            excluded_samples = ()

        sample_val_dict = json.loads(start_vars["sample_vals"])
        print(sample_val_dict)
        if sample_names is None:
            raise  NotImplementedError

        for sample in sample_names:
            if sample not in excluded_samples:
                value = sample_val_dict[sample]

                if not value.strip().lower() == "x":
                    self.sample_data[str(sample)] = float(value)

    def do_tissue_correlation_for_trait_list(self, tissue_dataset_id=1):
        """Given a list of correlation results (self.correlation_results),\
        gets the tissue correlation value for each"""
        # pylint: disable = E, W, R, C

        # Gets tissue expression values for the primary trait
        primary_trait_tissue_vals_dict = correlation_functions.get_trait_symbol_and_tissue_values(
            symbol_list=[self.this_trait.symbol])

        if self.this_trait.symbol.lower() in primary_trait_tissue_vals_dict:
            primary_trait_tissue_values = primary_trait_tissue_vals_dict[self.this_trait.symbol.lower(
            )]
            gene_symbol_list = [
                trait.symbol for trait in self.correlation_results if trait.symbol]

            corr_result_tissue_vals_dict = correlation_functions.get_trait_symbol_and_tissue_values(
                symbol_list=gene_symbol_list)

            for trait in self.correlation_results:
                if trait.symbol and trait.symbol.lower() in corr_result_tissue_vals_dict:
                    this_trait_tissue_values = corr_result_tissue_vals_dict[trait.symbol.lower(
                    )]

                    result = correlation_functions.cal_zero_order_corr_for_tiss(primary_trait_tissue_values,
                                                                                this_trait_tissue_values,
                                                                                self.corr_method)

                    trait.tissue_corr = result[0]
                    trait.tissue_pvalue = result[2]

    def do_lit_correlation_for_trait_list(self):
        # pylint: disable = E, W, R, C

        input_trait_mouse_gene_id = self.convert_to_mouse_gene_id(
            self.dataset.group.species.lower(), self.this_trait.geneid)

        for trait in self.correlation_results:

            if trait.geneid:
                trait.mouse_gene_id = self.convert_to_mouse_gene_id(
                    self.dataset.group.species.lower(), trait.geneid)
            else:
                trait.mouse_gene_id = None

            if trait.mouse_gene_id and str(trait.mouse_gene_id).find(";") == -1:
                result = g.db.execute(
                    """SELECT value
                       FROM LCorrRamin3
                       WHERE GeneId1='%s' and
                             GeneId2='%s'
                    """ % (escape(str(trait.mouse_gene_id)), escape(str(input_trait_mouse_gene_id)))
                ).fetchone()
                if not result:
                    result = g.db.execute("""SELECT value
                       FROM LCorrRamin3
                       WHERE GeneId2='%s' and
                             GeneId1='%s'
                    """ % (escape(str(trait.mouse_gene_id)), escape(str(input_trait_mouse_gene_id)))
                    ).fetchone()

                if result:
                    lit_corr = result.value
                    trait.lit_corr = lit_corr
                else:
                    trait.lit_corr = 0
            else:
                trait.lit_corr = 0

    def do_lit_correlation_for_all_traits(self):
        """method for lit_correlation for all traits"""
        # pylint: disable = E, W, R, C
        input_trait_mouse_gene_id = self.convert_to_mouse_gene_id(
            self.dataset.group.species.lower(), self.this_trait.geneid)

        lit_corr_data = {}
        for trait, gene_id in list(self.trait_geneid_dict.items()):
            mouse_gene_id = self.convert_to_mouse_gene_id(
                self.dataset.group.species.lower(), gene_id)

            if mouse_gene_id and str(mouse_gene_id).find(";") == -1:
                #print("gene_symbols:", input_trait_mouse_gene_id + " / " + mouse_gene_id)
                result = g.db.execute(
                    """SELECT value
                       FROM LCorrRamin3
                       WHERE GeneId1='%s' and
                             GeneId2='%s'
                    """ % (escape(mouse_gene_id), escape(input_trait_mouse_gene_id))
                ).fetchone()
                if not result:
                    result = g.db.execute("""SELECT value
                       FROM LCorrRamin3
                       WHERE GeneId2='%s' and
                             GeneId1='%s'
                    """ % (escape(mouse_gene_id), escape(input_trait_mouse_gene_id))
                    ).fetchone()
                if result:
                    #print("result:", result)
                    lit_corr = result.value
                    lit_corr_data[trait] = [gene_id, lit_corr]
                else:
                    lit_corr_data[trait] = [gene_id, 0]
            else:
                lit_corr_data[trait] = [gene_id, 0]

        lit_corr_data = collections.OrderedDict(sorted(list(lit_corr_data.items()),
                                                       key=lambda t: -abs(t[1][1])))

        return lit_corr_data

    def do_tissue_correlation_for_all_traits(self, tissue_dataset_id=1):
        # Gets tissue expression values for the primary trait
        # pylint: disable = E, W, R, C
        primary_trait_tissue_vals_dict = correlation_functions.get_trait_symbol_and_tissue_values(
            symbol_list=[self.this_trait.symbol])

        if self.this_trait.symbol.lower() in primary_trait_tissue_vals_dict:
            primary_trait_tissue_values = primary_trait_tissue_vals_dict[self.this_trait.symbol.lower(
            )]

            #print("trait_gene_symbols: ", pf(trait_gene_symbols.values()))
            corr_result_tissue_vals_dict = correlation_functions.get_trait_symbol_and_tissue_values(
                symbol_list=list(self.trait_symbol_dict.values()))

            #print("corr_result_tissue_vals: ", pf(corr_result_tissue_vals_dict))

            #print("trait_gene_symbols: ", pf(trait_gene_symbols))

            tissue_corr_data = {}
            for trait, symbol in list(self.trait_symbol_dict.items()):
                if symbol and symbol.lower() in corr_result_tissue_vals_dict:
                    this_trait_tissue_values = corr_result_tissue_vals_dict[symbol.lower(
                    )]

                    result = correlation_functions.cal_zero_order_corr_for_tiss(primary_trait_tissue_values,
                                                                                this_trait_tissue_values,
                                                                                self.corr_method)

                    tissue_corr_data[trait] = [symbol, result[0], result[2]]

            tissue_corr_data = collections.OrderedDict(sorted(list(tissue_corr_data.items()),
                                                              key=lambda t: -abs(t[1][1])))

    def get_sample_r_and_p_values(self, trait, target_samples):
        """Calculates the sample r (or rho) and p-value

        Given a primary trait and a target trait's sample values,
        calculates either the pearson r or spearman rho and the p-value
        using the corresponding scipy functions.

        """
        # pylint: disable = E, W, R, C
        self.this_trait_vals = []
        target_vals = []

        for index, sample in enumerate(self.target_dataset.samplelist):
            if sample in self.sample_data:
                sample_value = self.sample_data[sample]
                target_sample_value = target_samples[index]
                self.this_trait_vals.append(sample_value)
                target_vals.append(target_sample_value)

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

    def convert_to_mouse_gene_id(self, species=None, gene_id=None):
        """If the species is rat or human, translate the gene_id to the mouse geneid

        If there is no input gene_id or there's no corresponding mouse gene_id, return None

        """
        if not gene_id:
            return None

        mouse_gene_id = None
        if "species" == "mouse":
            mouse_gene_id = gene_id

        elif species == 'rat':
            query = """SELECT mouse
                   FROM GeneIDXRef
                   WHERE rat='%s'""" % escape(gene_id)

            result = g.db.execute(query).fetchone()
            if result != None:
                mouse_gene_id = result.mouse

        elif species == "human":

            query = """SELECT mouse
                   FROM GeneIDXRef
                   WHERE human='%s'""" % escape(gene_id)

            result = g.db.execute(query).fetchone()
            if result != None:
                mouse_gene_id = result.mouse

        return mouse_gene_id

    def do_correlation(self, start_vars, create_dataset=create_dataset,
                       create_trait=create_trait,
                       get_species_dataset_trait=get_species_dataset_trait):
        # pylint: disable = E, W, R, C
        # probably refactor start_vars being passed twice
        # this method  aims to replace the do_correlation but also add dependendency injection
        # to enable testing

        # should maybe refactor below code more or less works the same
        if start_vars["dataset"] == "Temp":
            self.dataset = create_dataset(
                dataset_name="Temp", dataset_type="Temp", group_name=start_vars['group'])

            self.trait_id = start_vars["trait_id"]

            self.this_trait = create_trait(dataset=self.dataset,
                                           name=self.trait_id,
                                           cellid=None)

        else:

            get_species_dataset_trait(self, start_vars)

        corr_samples_group = start_vars['corr_samples_group']
        self.sample_data = {}
        self.corr_type = start_vars['corr_type']
        self.corr_method = start_vars['corr_sample_method']
        self.min_expr = float(
            start_vars["min_expr"]) if start_vars["min_expr"] != "" else None
        self.p_range_lower = float(
            start_vars["p_range_lower"]) if start_vars["p_range_lower"] != "" else -1.0
        self.p_range_upper = float(
            start_vars["p_range_upper"]) if start_vars["p_range_upper"] != "" else 1.0

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
                
            # print("primary samples are *****",primary_samples)

            self.process_samples(start_vars, primary_samples)

        if corr_samples_group != 'samples_primary':
            if corr_samples_group == 'samples_other':
                primary_samples = [x for x in primary_samples if x not in (
                    self.dataset.group.parlist + self.dataset.group.f1list)]

            self.process_samples(start_vars, list(self.this_trait.data.keys()), primary_samples)

        self.target_dataset = create_dataset(start_vars['corr_dataset'])
        # when you add code to retrieve the trait_data for target dataset got gets very slow
        import time

        init_time = time.time()
        self.target_dataset.get_trait_data(list(self.sample_data.keys()))

        aft_time = time.time() - init_time

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

        if self.corr_type == "tissue":
            self.trait_symbol_dict = self.dataset.retrieve_genes("Symbol")

            tissue_corr_data = self.do_tissue_correlation_for_all_traits()
            if tissue_corr_data != None:
                for trait in list(tissue_corr_data.keys())[:self.return_number]:
                    self.get_sample_r_and_p_values(
                        trait, self.target_dataset.trait_data[trait])
            else:
                for trait, values in list(self.target_dataset.trait_data.items()):
                    self.get_sample_r_and_p_values(trait, values)

        elif self.corr_type == "lit":
            self.trait_geneid_dict = self.dataset.retrieve_genes("GeneId")
            lit_corr_data = self.do_lit_correlation_for_all_traits()

            for trait in list(lit_corr_data.keys())[:self.return_number]:
                self.get_sample_r_and_p_values(
                    trait, self.target_dataset.trait_data[trait])

        elif self.corr_type == "sample":
            for trait, values in list(self.target_dataset.trait_data.items()):
                self.get_sample_r_and_p_values(trait, values)

        self.correlation_data = collections.OrderedDict(sorted(list(self.correlation_data.items()),
                                                               key=lambda t: -abs(t[1][0])))

        # ZS: Convert min/max chromosome to an int for the location range option

        """
        took 20.79 seconds took compute all the above majority of time taken on retrieving target dataset trait
        info
        """

        initial_time_chr = time.time()

        range_chr_as_int = None
        for order_id, chr_info in list(self.dataset.species.chromosomes.chromosomes.items()):
            if 'loc_chr' in start_vars:
                if chr_info.name == self.location_chr:
                    range_chr_as_int = order_id

        for _trait_counter, trait in enumerate(list(self.correlation_data.keys())[:self.return_number]):
            trait_object = create_trait(
                dataset=self.target_dataset, name=trait, get_qtl_info=True, get_sample_info=False)
            if not trait_object:
                continue

            chr_as_int = 0
            for order_id, chr_info in list(self.dataset.species.chromosomes.chromosomes.items()):
                if self.location_type == "highest_lod":
                    if chr_info.name == trait_object.locus_chr:
                        chr_as_int = order_id
                else:
                    if chr_info.name == trait_object.chr:
                        chr_as_int = order_id

            if (float(self.correlation_data[trait][0]) >= self.p_range_lower and
                    float(self.correlation_data[trait][0]) <= self.p_range_upper):

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

        """
        above takes time with respect to size of traits i.e n=100,500,.....t_size
        """

        if self.corr_type != "lit" and self.dataset.type == "ProbeSet" and self.target_dataset.type == "ProbeSet":
            # self.do_lit_correlation_for_trait_list()
            self.do_lit_correlation_for_trait_list()

        if self.corr_type != "tissue" and self.dataset.type == "ProbeSet" and self.target_dataset.type == "ProbeSet":
            self.do_tissue_correlation_for_trait_list()
            # self.do_lit_correlation_for_trait_list()

        self.json_results = generate_corr_json(
            self.correlation_results, self.this_trait, self.dataset, self.target_dataset)

        # org mode by bons

        # DVORAKS
        # klavaro for touch typing
        # archwiki for documentation
        # exwm for window manager ->13

        # will fit perfectly with genenetwork 2 with change of anything if return self

        # alternative for this
        return self
        # return {
        #     # "Results": "succeess",
        #     # "return_number": self.return_number,
        #     # "primary_samples": primary_samples,
        #     # "time_taken": 12,
        #     # "correlation_data": self.correlation_data,
        #     "correlation_json": self.json_results
        # }


def do_bicor(this_trait_vals, target_trait_vals):
    # pylint: disable = E, W, R, C
    r_library = ro.r["library"]             # Map the library function
    r_options = ro.r["options"]             # Map the options function

    r_library("WGCNA")
    r_bicor = ro.r["bicorAndPvalue"]        # Map the bicorAndPvalue function

    r_options(stringsAsFactors=False)

    this_vals = ro.Vector(this_trait_vals)
    target_vals = ro.Vector(target_trait_vals)

    the_r, the_p, _fisher_transform, _the_t, _n_obs = [
        numpy.asarray(x) for x in r_bicor(x=this_vals, y=target_vals)]

    return the_r, the_p


def get_header_fields(data_type, corr_method):
    """function to get header fields when doing correlation"""
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
    """function to generate corr json data"""
    #todo refactor this function
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
