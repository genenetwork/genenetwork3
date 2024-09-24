"""Helper functions to access wiki entries"""

from typing import Dict, List

from MySQLdb.cursors import DictCursor


class MissingDBDataException(Exception):
    """Error due to DB missing some data"""


def _decode_dict(result: dict):
    new_result = {}
    for key, val in result.items():
        if isinstance(val, bytes):
            new_result[key] = val.decode()
        else:
            new_result[key] = val
    return new_result


def get_latest_comment(connection, comment_id: int) -> int:
    """ Latest comment is one with the highest versionId """
    cursor = connection.cursor(DictCursor)
    query = """ SELECT versionId AS version, symbol, PubMed_ID AS pubmed_ids, sp.Name AS species,
        comment, email, weburl, initial, reason
        FROM `GeneRIF` gr
		INNER JOIN Species sp USING(SpeciesId)
		WHERE gr.Id = %s
		ORDER BY versionId DESC LIMIT 1;
    """
    cursor.execute(query, (str(comment_id),))
    result = _decode_dict(cursor.fetchone())
    if (pubmed_ids := result.get("pubmed_ids")) is None:
        pubmed_ids = ""
    result["pubmed_ids"] = [x.strip() for x in pubmed_ids.split()]
    categories_query = """
        SELECT grx.GeneRIFId, grx.versionId, gc.Name FROM GeneRIFXRef grx
                INNER JOIN GeneCategory gc ON grx.GeneCategoryId=gc.Id
                WHERE GeneRIFId = %s AND versionId=%s;
    """

    cursor.execute(categories_query, (str(comment_id), result["version"]))
    categories = [_decode_dict(x) for x in cursor.fetchall()]
    result["categories"] = [x["Name"] for x in categories]
    return result


def get_species_id(cursor, species_name: str) -> int:
    """Find species id given species `Name`"""
    cursor.execute(
        "SELECT SpeciesID from Species  WHERE Name = %s", (species_name,))
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
        raise MissingDBDataException(
            f"No comment found with comment_id={comment_id}")
    return latest_version + 1


def get_categories_ids(cursor, categories: List[str]) -> List[int]:
    """Get the categories_ids from a list of category strings"""
    dict_cats = get_categories(cursor)
    category_ids = []
    for category in set(categories):
        cat_id = dict_cats.get(category.strip())
        if cat_id is None:
            raise MissingDBDataException(
                f"Category with Name={category} not found")
        category_ids.append(cat_id)
    return category_ids


def get_categories(cursor) -> Dict[str, int]:
    """Get all categories"""
    cursor.execute("SELECT Name, Id from GeneCategory")
    raw_categories = cursor.fetchall()
    dict_cats = dict(raw_categories)
    return dict_cats


def get_species(cursor) -> Dict[str, str]:
    """Get all species"""
    cursor.execute("SELECT Name, SpeciesName from Species")
    raw_species = cursor.fetchall()
    dict_cats = dict(raw_species)
    return dict_cats
