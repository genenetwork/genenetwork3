"""Functions and utilities to use when generating queries"""

def mapping_to_query_columns(mapping_dict: dict[str, str]) -> tuple[str, ...]:
    """
    Internal function to convert mapping dicts into column clauses for queries.
    """
    return tuple(f"{tcol} as {dcol}" for dcol, tcol in mapping_dict.items())
