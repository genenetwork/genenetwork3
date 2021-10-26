"""This module contains db functions that get data related to species or
groups. Particularly useful when generating the menu

"""
from typing import Any, Optional, Tuple
from MySQLdb import escape_string


def get_all_species(conn: Any) -> Optional[Tuple]:
    """Return a list of all species"""
    with conn.cursor() as cursor:
        cursor.execute("SELECT Name, MenuName FROM Species "
                       "ORDER BY OrderId")
        return cursor.fetchall()


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

def translate_to_mouse_gene_id(species: str, geneid: int, conn: Any) -> int:
    """
    Translate rat or human geneid to mouse geneid

    This is a migration of the
    `web.webqtl.correlation/CorrelationPage.translateToMouseGeneID` function in
    GN1
    """
    assert species in ("rat", "mouse", "human"), "Invalid species"
    if geneid is None:
        return 0

    if species == "mouse":
        return geneid

    with conn.cursor as cursor:
        if species == "rat":
            cursor.execute(
                "SELECT mouse FROM GeneIDXRef WHERE rat = %s", geneid)
            rat_geneid = cursor.fetchone()
            if rat_geneid:
                return rat_geneid[0]

        cursor.execute(
            "SELECT mouse FROM GeneIDXRef WHERE human = %s", geneid)
        human_geneid = cursor.fetchone()
        if human_geneid:
            return human_geneid[0]

    return 0 # default if all else fails
