"""module contains code for doing correlation"""


class CorrelationResults:
    def __init__(self, start_vars):
    	self.assertion_for_start_vars(start_vars)
    	# if no assertion error is raised do  

    	self.do_correlation(start_vars)





    @staticmethod
    def assertion_for_start_vars(start_vars):
        # example includes sample
        assert("corr_type" in start_vars)
        assert(is_str(start_vars['corr_type']))
        # example includes pearson
        assert('corr_sample_method' in start_vars)
        assert('corr_dataset' in start_vars)
        # means the  limit
        assert('corr_return_results' in start_vars)

        if "loc_chr" in start_vars:
        	assert('min_loc_mb' in start_vars)
        	assert('max_loc_mb' in start_vars)



    def do_correlation(self,start_vars):

    	return {
    	 "success":"data"
    	}


        # code for doing correlation starts here




# class CorrelationResults(object):
#     def __init__(self, start_vars):
#         # get trait list from db (database name)
#         # calculate correlation with Base vector and targets

#         # Check parameters
#         assert('corr_type' in start_vars)
#         assert(is_str(start_vars['corr_type']))
#         assert('dataset' in start_vars)
#         # assert('group' in start_vars) permitted to be empty?
#         assert('corr_sample_method' in start_vars)
#         assert('corr_samples_group' in start_vars)
#         assert('corr_dataset' in start_vars)
#         assert('corr_return_results' in start_vars)
#         if 'loc_chr' in start_vars:
#             assert('min_loc_mb' in start_vars)
#             assert('max_loc_mb' in start_vars)

#         with Bench("Doing correlations"):
#             if start_vars['dataset'] == "Temp":
#                 self.dataset = data_set.create_dataset(
#                     dataset_name="Temp", dataset_type="Temp", group_name=start_vars['group'])
#                 self.trait_id = start_vars['trait_id']
#                 self.this_trait = create_trait(dataset=self.dataset,
#                                                name=self.trait_id,
#                                                cellid=None)
#             else:
#                 helper_functions.get_species_dataset_trait(self, start_vars)

#             corr_samples_group = start_vars['corr_samples_group']

#             self.sample_data = {}
#             self.corr_type = start_vars['corr_type']
#             self.corr_method = start_vars['corr_sample_method']
#             self.min_expr = get_float(start_vars, 'min_expr')
#             self.p_range_lower = get_float(start_vars, 'p_range_lower', -1.0)
#             self.p_range_upper = get_float(start_vars, 'p_range_upper', 1.0)

#             if ('loc_chr' in start_vars and
#                 'min_loc_mb' in start_vars and
#                     'max_loc_mb' in start_vars):

#                 self.location_type = get_string(start_vars, 'location_type')
#                 self.location_chr = get_string(start_vars, 'loc_chr')
#                 self.min_location_mb = get_int(start_vars, 'min_loc_mb')
#                 self.max_location_mb = get_int(start_vars, 'max_loc_mb')
#             else:
#                 self.location_type = self.location_chr = self.min_location_mb = self.max_location_mb = None

#             self.get_formatted_corr_type()
#             self.return_number = int(start_vars['corr_return_results'])

#             # The two if statements below append samples to the sample list based upon whether the user
#             # rselected Primary Samples Only, Other Samples Only, or All Samples

#             primary_samples = self.dataset.group.samplelist
#             if self.dataset.group.parlist != None:
#                 primary_samples += self.dataset.group.parlist
#             if self.dataset.group.f1list != None:
#                 primary_samples += self.dataset.group.f1list

#             # If either BXD/whatever Only or All Samples, append all of that group's samplelist
#             if corr_samples_group != 'samples_other':
#                 self.process_samples(start_vars, primary_samples)

#             # If either Non-BXD/whatever or All Samples, get all samples from this_trait.data and
#             # exclude the primary samples (because they would have been added in the previous
#             # if statement if the user selected All Samples)
#             if corr_samples_group != 'samples_primary':
#                 if corr_samples_group == 'samples_other':
#                     primary_samples = [x for x in primary_samples if x not in (
#                         self.dataset.group.parlist + self.dataset.group.f1list)]
#                 self.process_samples(start_vars, list(
#                     self.this_trait.data.keys()), primary_samples)

#             self.target_dataset = data_set.create_dataset(
#                 start_vars['corr_dataset'])
#             self.target_dataset.get_trait_data(list(self.sample_data.keys()))

#             self.header_fields = get_header_fields(
#                 self.target_dataset.type, self.corr_method)

#             if self.target_dataset.type == "ProbeSet":
#                 self.filter_cols = [7, 6]
#             elif self.target_dataset.type == "Publish":
#                 self.filter_cols = [6, 0]
#             else:
#                 self.filter_cols = [4, 0]

#             self.correlation_results = []

#             self.correlation_data = {}

#             if self.corr_type == "tissue":
#                 self.trait_symbol_dict = self.dataset.retrieve_genes("Symbol")

#                 tissue_corr_data = self.do_tissue_correlation_for_all_traits()
#                 if tissue_corr_data != None:
#                     for trait in list(tissue_corr_data.keys())[:self.return_number]:
#                         self.get_sample_r_and_p_values(
#                             trait, self.target_dataset.trait_data[trait])
#                 else:
#                     for trait, values in list(self.target_dataset.trait_data.items()):
#                         self.get_sample_r_and_p_values(trait, values)

#             elif self.corr_type == "lit":
#                 self.trait_geneid_dict = self.dataset.retrieve_genes("GeneId")
#                 lit_corr_data = self.do_lit_correlation_for_all_traits()

#                 for trait in list(lit_corr_data.keys())[:self.return_number]:
#                     self.get_sample_r_and_p_values(
#                         trait, self.target_dataset.trait_data[trait])

#             elif self.corr_type == "sample":
#                 for trait, values in list(self.target_dataset.trait_data.items()):
#                     self.get_sample_r_and_p_values(trait, values)

#             self.correlation_data = collections.OrderedDict(sorted(list(self.correlation_data.items()),
#                                                                    key=lambda t: -abs(t[1][0])))

#             # ZS: Convert min/max chromosome to an int for the location range option
#             range_chr_as_int = None
#             for order_id, chr_info in list(self.dataset.species.chromosomes.chromosomes.items()):
#                 if 'loc_chr' in start_vars:
#                     if chr_info.name == self.location_chr:
#                         range_chr_as_int = order_id

#             for _trait_counter, trait in enumerate(list(self.correlation_data.keys())[:self.return_number]):
#                 trait_object = create_trait(
#                     dataset=self.target_dataset, name=trait, get_qtl_info=True, get_sample_info=False)
#                 if not trait_object:
#                     continue

#                 chr_as_int = 0
#                 for order_id, chr_info in list(self.dataset.species.chromosomes.chromosomes.items()):
#                     if self.location_type == "highest_lod":
#                         if chr_info.name == trait_object.locus_chr:
#                             chr_as_int = order_id
#                     else:
#                         if chr_info.name == trait_object.chr:
#                             chr_as_int = order_id

#                 if (float(self.correlation_data[trait][0]) >= self.p_range_lower and
#                         float(self.correlation_data[trait][0]) <= self.p_range_upper):

#                     if (self.target_dataset.type == "ProbeSet" or self.target_dataset.type == "Publish") and bool(trait_object.mean):
#                         if (self.min_expr != None) and (float(trait_object.mean) < self.min_expr):
#                             continue

#                     if range_chr_as_int != None and (chr_as_int != range_chr_as_int):
#                         continue
#                     if self.location_type == "highest_lod":
#                         if (self.min_location_mb != None) and (float(trait_object.locus_mb) < float(self.min_location_mb)):
#                             continue
#                         if (self.max_location_mb != None) and (float(trait_object.locus_mb) > float(self.max_location_mb)):
#                             continue
#                     else:
#                         if (self.min_location_mb != None) and (float(trait_object.mb) < float(self.min_location_mb)):
#                             continue
#                         if (self.max_location_mb != None) and (float(trait_object.mb) > float(self.max_location_mb)):
#                             continue

#                     (trait_object.sample_r,
#                      trait_object.sample_p,
#                      trait_object.num_overlap) = self.correlation_data[trait]

#                     # Set some sane defaults
#                     trait_object.tissue_corr = 0
#                     trait_object.tissue_pvalue = 0
#                     trait_object.lit_corr = 0
#                     if self.corr_type == "tissue" and tissue_corr_data != None:
#                         trait_object.tissue_corr = tissue_corr_data[trait][1]
#                         trait_object.tissue_pvalue = tissue_corr_data[trait][2]
#                     elif self.corr_type == "lit":
#                         trait_object.lit_corr = lit_corr_data[trait][1]

#                     self.correlation_results.append(trait_object)

#             if self.corr_type != "lit" and self.dataset.type == "ProbeSet" and self.target_dataset.type == "ProbeSet":
#                 self.do_lit_correlation_for_trait_list()

#             if self.corr_type != "tissue" and self.dataset.type == "ProbeSet" and self.target_dataset.type == "ProbeSet":
#                 self.do_tissue_correlation_for_trait_list()

#         self.json_results = generate_corr_json(
#             self.correlation_results, self.this_trait, self.dataset, self.target_dataset)
