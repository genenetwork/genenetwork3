"""Tests gn3.db.genotypes"""
from unittest import TestCase
from gn3.db.genotypes import parse_genotype_labels, parse_genotype_header

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

    def test_parse_genotype_header(self):
        for header, expected in [
                [("Chr\tLocus\tcM\tMb\tBXD1\tBXD2\tBXD5\tBXD6\tBXD8\tBXD9\t"
                  "BXD11\tBXD12\tBXD13\tBXD14\tBXD15\tBXD16\tBXD18\tBXD19"),
                 (("Mbmap", True), ("cm_column", 2), ("mb_column", 3),
                  ("prgy",
                   ("BXD1", "BXD2", "BXD5", "BXD6", "BXD8", "BXD9", "BXD11",
                    "BXD12", "BXD13", "BXD14", "BXD15", "BXD16", "BXD18",
                    "BXD19")),
                  ("nprgy", 14))],
                [("Chr\tLocus\tcM\tBXD1\tBXD2\tBXD5\tBXD6\tBXD8\tBXD9\tBXD11"
                  "\tBXD12\tBXD13\tBXD14\tBXD15\tBXD16\tBXD18"),
                 (("Mbmap", False), ("cm_column", 2), ("mb_column", None),
                  ("prgy",
                   ("BXD1", "BXD2", "BXD5", "BXD6", "BXD8", "BXD9", "BXD11",
                    "BXD12", "BXD13", "BXD14", "BXD15", "BXD16", "BXD18")),
                  ("nprgy", 13))]]:
            with self.subTest(header=header):
                self.assertEqual(parse_genotype_header(header), expected)
