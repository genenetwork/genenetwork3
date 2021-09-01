"""Tests gn3.db.genotypes"""
from unittest import TestCase
from gn3.db.genotypes import parse_genotype_labels

class TestGenotypes(TestCase):
    """Tests for functions in `gn3.db.genotypes`."""

    def test_parse_genotype_labels(self):
        self.assertEqual(
            parse_genotype_labels([
                "@name: test_group\t", "@filler: test_filler    ",
                "@type:test_type", "@mat:test_mat   \t", "@pat:test_pat ",
                "@het: test_het ", "@unk: test_unk", "@other: test_other",
                "@brrr: test_brrr "]),
        (("group", "test_group"), ("filler", "test_filler"),
         ("type", "test_type"), ("mat", "test_mat"), ("pat", "test_pat"),
         ("het", "test_het"), ("unk", "test_unk")))
