"""module contains species and chromosomes classes"""
import collections

from flask import g


from gn3.utility.logger import getLogger
logger = getLogger(__name__)

 # pylint: disable=too-few-public-methods
 # intentionally disabled check for few public methods

class TheSpecies:
    """class for Species"""

    def __init__(self, dataset=None, species_name=None):
        if species_name is not None:
            self.name = species_name
            self.chromosomes = Chromosomes(species=self.name)
        else:
            self.dataset = dataset
            self.chromosomes = Chromosomes(dataset=self.dataset)



class IndChromosome:
    """class for IndChromosome"""

    def __init__(self, name, length):
        self.name = name
        self.length = length

    @property
    def mb_length(self):
        """Chromosome length in megabases"""
        return self.length / 1000000




class Chromosomes:
    """class for Chromosomes"""

    def __init__(self, dataset=None, species=None):
        self.chromosomes = collections.OrderedDict()
        if species is not None:
            query = """
                Select
                        Chr_Length.Name, Chr_Length.OrderId, Length from Chr_Length, Species
                where
                        Chr_Length.SpeciesId = Species.SpeciesId AND
                        Species.Name = '%s'
                Order by OrderId
                """ % species.capitalize()
        else:
            self.dataset = dataset

            query = """
                Select
                        Chr_Length.Name, Chr_Length.OrderId, Length from Chr_Length, InbredSet
                where
                        Chr_Length.SpeciesId = InbredSet.SpeciesId AND
                        InbredSet.Name = '%s'
                Order by OrderId
                """ % self.dataset.group.name
        logger.sql(query)
        results = g.db.execute(query).fetchall()

        for item in results:
            self.chromosomes[item.OrderId] = IndChromosome(
                item.Name, item.Length)
