"""This module contains db functions that get data related to species or
groups. Particularly useful when generating the menu

"""
from typing import Any, Optional, Tuple
from MySQLdb import escape_string


def get_all_species(conn: Any) -> Optional[Tuple]:
    """Return a list of all species"""
    with conn.cursor() as cursor:
        cursor.execute("SELECT Name, MenuName, IFNULL(Family, 'None') "
                       "FROM Species "
                       "ORDER BY IFNULL(FamilyOrderId, SpeciesName) ASC, "
                       "IFNULL(Family, SpeciesName) ASC, "
                       "OrderId ASC")
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
        query = {
            "rat": "SELECT mouse FROM GeneIDXRef WHERE rat = %s",
            "human": "SELECT mouse FROM GeneIDXRef WHERE human = %s"
        }
        cursor.execute(query[species], geneid)
        translated_gene_id = cursor.fetchone()
        if translated_gene_id:
            return translated_gene_id[0]

    return 0 # default if all else fails

def species_name(conn: Any, group: str) -> str:
    """
    Retrieve the name of the species, given the group (RISet).

    This is a migration of the
    `web.webqtl.dbFunction.webqtlDatabaseFunction.retrieveSpecies` function in
    GeneNetwork1.
    """
    with conn.cursor() as cursor:
        cursor.execute(
            ("SELECT Species.Name FROM Species, InbredSet "
             "WHERE InbredSet.Name = %(group_name)s "
             "AND InbredSet.SpeciesId = Species.Id"),
            {"group_name": group})
        return cursor.fetchone()[0]
    return None
