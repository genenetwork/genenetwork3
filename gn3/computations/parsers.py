"""Parsers for generating some files in genenetwork"""
import os
from typing import Any, Dict, List, Tuple


def parse_genofile(file_path: str) -> Tuple[List[str],
                                            List[Dict[str, Any]]]:
    """Parse a genotype file with a given format"""
    if not os.path.exists(file_path):
        raise FileNotFoundError
    __map = {
        'b': -1,
        'd': 1,
        'h': 0,
        'u': None,
    }
    genotypes, samples = [], []
    with open(file_path, "r", encoding="utf-8") as _genofile:
        for line in _genofile:
            line = line.strip()
            if line.startswith(("#", "@")):
                continue
            cells = line.split()
            if line.startswith("Chr"):
                samples = cells[4:]
                samples = [sample.lower() for sample in samples]
                continue
            values = [__map.get(value.lower(), None) for value in cells[4:]]
            genotype = {
                "chr": cells[0],
                "locus": cells[1],
                "cm": cells[2],
                "mb": cells[3],
                "values":  values,
                "dicvalues": dict(zip(samples, values)),
            }
            genotypes.append(genotype)
        return samples, genotypes
