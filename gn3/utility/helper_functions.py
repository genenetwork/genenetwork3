
from gn3.base.data_set import create_dataset
from gn3.base.species import TheSpecies

def get_species_dataset_trait(self, start_vars):
    print("CALLING THIS FUNCTION HERE ")
    if "temp_trait" in list(start_vars.keys()):
        if start_vars['temp_trait'] == "True":
            self.dataset = create_dataset(
                dataset_name="Temp", dataset_type="Temp", group_name=start_vars['group'])

        else:
            self.dataset = create_dataset(start_vars['dataset'])

    else:
        self.dataset = create_dataset(start_vars['dataset'])

    # logger.debug("After creating dataset")
    # self.species = TheSpecies(dataset=self.dataset)
    # # logger.debug("After creating species")

    # self.this_trait = create_trait(dataset=self.dataset,
    #                                name=start_vars['trait_id'],
    #                                cellid=None,
    #                                get_qtl_info=True)

    # logger.debug("After creating trait")
