"""Helper functions to access wiki entries"""

from typing import List


class MissingDBDataException(Exception):
    """Error due to DB missing some data"""


def get_species_id(cursor, species_name: str) -> int:
    """Find species id given species `Name`"""
    cursor.execute("SELECT SpeciesID from Species  WHERE Name = %s", (species_name,))
    species_ids = cursor.fetchall()
    if len(species_ids) != 1:
        raise MissingDBDataException(
            f"expected 1 species with Name={species_name} but found {len(species_ids)}!"
        )
    return species_ids[0][0]


def get_next_comment_version(cursor, comment_id: int) -> int:
    """Find the version to add, usually latest_version + 1"""
    cursor.execute(
        "SELECT MAX(versionId) as version_id from GeneRIF WHERE Id = %s", (comment_id,)
    )
    latest_version = cursor.fetchone()[0]
    if latest_version is None:
        raise MissingDBDataException(f"No comment found with comment_id={comment_id}")
    return latest_version + 1


def get_categories_ids(cursor, categories: List[str]) -> List[int]:
    """Get the categories_ids from a list of category strings"""
    cursor.execute("SELECT Name, Id from GeneCategory")
    raw_categories = cursor.fetchall()
    dict_cats = dict(raw_categories)
    category_ids = []
    for category in set(categories):
        cat_id = dict_cats.get(category.strip())
        if cat_id is None:
            raise MissingDBDataException(f"Category with Name={category} not found")
        category_ids.append(cat_id)
    return category_ids
