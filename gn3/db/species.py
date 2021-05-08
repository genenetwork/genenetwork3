"""This module contains db functions that get data related to species or
groups. Particularly useful when generating the menu

"""
from typing import Any, Optional, Tuple
from MySQLdb import escape_string


def get_chromosome(name: str, is_species: bool, conn: Any) -> Optional[Tuple]:
    """Given either a group or a species Name, return all the species"""
    _sql = ("SELECT Chr_Length.Name, Chr_Length.OrderId, "
            "Length FROM Chr_Length, Species WHERE "
            "Chr_Length.SpeciesId = Species.SpeciesId AND "
            "Species.Name = "
            f"'{escape_string(name).decode('UTF-8')}' ORDER BY OrderId")
    if not is_species:
        _sql = ("SELECT Chr_Length.Name, Chr_Length.OrderId, "
                "Length FROM Chr_Length, InbredSet WHERE "
                "Chr_Length.SpeciesId = InbredSet.SpeciesId AND "
                "InbredSet.Name = "
                f"'{escape_string(name).decode('UTF-8')}' ORDER BY OrderId")
    with conn.cursor() as cursor:
        cursor.execute(_sql)
        return cursor.fetchall()
