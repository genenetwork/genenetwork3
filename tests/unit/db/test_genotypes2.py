"""Module to test functions in gn3.db.genotypes"""

import pytest

from gn3.db.genotypes import load_genotype_samples

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "genotype_filename,file_type,expected", (
        ("tests/unit/test_data/genotype.txt", "geno", ("BXD1","BXD2")),))
def test_load_genotype_samples(genotype_filename, file_type, expected):
    """Test that the genotype samples are loaded correctly"""
    assert load_genotype_samples(genotype_filename, file_type) == expected
