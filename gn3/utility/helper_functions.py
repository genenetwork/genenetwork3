"""module contains general helper functions """
from gn3.base.data_set import create_dataset
from gn3.base.trait import create_trait
from gn3.base.species import TheSpecies


def get_species_dataset_trait(self, start_vars):
    """function to get species dataset and trait"""
    if "temp_trait" in list(start_vars.keys()):
        if start_vars['temp_trait'] == "True":
            self.dataset = create_dataset(
                dataset_name="Temp", dataset_type="Temp", group_name=start_vars['group'])

        else:
            self.dataset = create_dataset(start_vars['dataset'])

    else:
        self.dataset = create_dataset(start_vars['dataset'])
    self.species = TheSpecies(dataset=self.dataset)

    self.this_trait = create_trait(dataset=self.dataset,
                                   name=start_vars['trait_id'],
                                   cellid=None,
                                   get_qtl_info=True)
