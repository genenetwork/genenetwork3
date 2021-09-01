"""Tests gn3.db.genotypes"""
from unittest import TestCase
from gn3.db.genotypes import (
    parse_genotype_file,
    parse_genotype_labels,
    parse_genotype_header,
    parse_genotype_marker,
    build_genotype_chromosomes)

class TestGenotypes(TestCase):
    """Tests for functions in `gn3.db.genotypes`."""

    def test_parse_genotype_labels(self):
        """Test that the genotype labels are parsed correctly."""
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
        """Test that the genotype header is parsed correctly."""
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

    def test_parse_genotype_data_line(self):
        """Test parsing of data lines."""
        for line, geno_obj, parlist, expected in [
                ["1\trs31443144\t1.50\t3.010274\tB\tB\tD\tD\tD\tB\tB\tD\tB\tB",
                 {"mat": "test_mat", "pat": "test_pat", "het": "test_het",
                  "unk": "test_unk", "cm_column": 2, "Mbmap": True,
                  "mb_column": 3},
                 tuple(),
                 (("chr", "1"), ("name", "rs31443144"), ("cM", 2.0),
                  ("Mb", 3.0),
                  ("genotype",
                   ("U", "U", "U", "U", "U", "U", "U", "U", "U", "U")))],
                ["1\trs31443144\t1.50\t3.010274\tB\tB\tD\tD\tD\tB\tB\tD\tB\tB",
                 {"mat": "test_mat", "pat": "test_pat", "het": "test_het",
                  "unk": "test_unk", "cm_column": 2, "Mbmap": True,
                  "mb_column": 3},
                 ("some", "parlist", "content"),
                 (("chr", "1"), ("name", "rs31443144"), ("cM", 2.0),
                  ("Mb", 3.0),
                  ("genotype",
                   (-1, 1, "U", "U", "U", "U", "U", "U", "U", "U")))],
                ["1\trs31443144\t1.50\t3.010274\tB\tB\tD\tH\tD\tB\tU\tD\tB\tB",
                 {"mat": "B", "pat": "D", "het": "H", "unk": "U",
                  "cm_column": 2, "Mbmap": True, "mb_column": 3},
                 tuple(),
                 (("chr", "1"), ("name", "rs31443144"), ("cM", 2.0),
                  ("Mb", 3.0),
                  ("genotype", (-1, -1, 1, 0, 1, -1, "U", 1, -1, -1)))]]:
            with self.subTest(line = line):
                self.assertEqual(
                    parse_genotype_marker(line, geno_obj, parlist),
                    expected)

    def test_build_genotype_chromosomes(self):
        """
        Given `markers` and `geno_obj`, test that `build_genotype_chromosomes`
        builds a sequence of chromosomes with the given markers ordered
        according to the `chr` value."""
        for markers, geno_obj, expected in [
                [[(("chr", "1"), ("name", "rs31443144"), ("cM", 2.0),
                   ("Mb", 3.0),
                   ("genotype", (-1, -1, 1, 0, 1, -1, "U", 1, -1, -1))),
                  (("chr", "2"), ("name", "rs31443144"), ("cM", 2.0),
                   ("Mb", 3.0),
                   ("genotype", (-1, -1, 1, 0, 1, -1, "U", 1, -1, -1)))],
                 {"mat": "B", "pat": "D", "het": "H", "unk": "U",
                  "cm_column": 2, "Mbmap": True, "mb_column": 3},
                 ((("name", "1"), ("mb_exists", True), ("cm_column", 2),
                   ("mb_column", 3),
                   ("loci",
                    ({"chr": "1", "name": "rs31443144", "cM": 2.0, "Mb": 3.0,
                      "genotype": (-1, -1, 1, 0, 1, -1, "U", 1, -1, -1)},))),
                  (("name", "2"), ("mb_exists", True), ("cm_column", 2),
                   ("mb_column", 3),
                   ("loci",
                    ({"chr": "2", "name": "rs31443144", "cM": 2.0, "Mb": 3.0,
                      "genotype": (-1, -1, 1, 0, 1, -1, "U", 1, -1, -1)},))))],
                [[(("chr", "1"), ("name", "rs31443144"), ("cM", 2.0),
                   ("Mb", None),
                   ("genotype", (-1, 1, 1, 0, 1, -1, "U", 1, -1, -1)))],
                 {"mat": "B", "pat": "D", "het": "H", "unk": "U",
                  "cm_column": 2, "Mbmap": False, "mb_column": None},
                 ((("name", "1"), ("mb_exists", False), ("cm_column", 2),
                   ("mb_column", None),
                   ("loci",
                    ({"chr": "1", "name": "rs31443144", "cM": 2.0, "Mb": None,
                      "genotype": (-1, 1, 1, 0, 1, -1, "U", 1, -1, -1)},))),)]]:
            with self.subTest(markers = markers):
                self.assertEqual(
                    build_genotype_chromosomes(geno_obj, markers),
                    expected)

    def test_parse_genotype_file(self):
        """Test the parsing of genotype files. """
        self.assertEqual(
            parse_genotype_file(
                "tests/unit/db/data/genotypes/genotype_sample1.geno"),
            {"group": "BXD",
             "type": "riset",
             "mat": "B",
             "pat": "D",
             "het": "H",
             "unk": "U",
             "Mbmap": True,
             "cm_column": 2,
             "mb_column": 3,
             "prgy": ("BXD1", "BXD2", "BXD5", "BXD6", "BXD8", "BXD9"),
             "nprgy": 6,
             "chromosomes": (
                 {"name": "1",
                  "mb_exists": True,
                  "cm_column": 2,
                  "mb_column": 3,
                  "loci": (
                      {"chr": "1",
                       "name": "rs31443144",
                       "cM": 2.0,
                       "Mb": 3.0,
                       "genotype": (-1, -1, 1, 1, 1, -1)
                       },
                      {"chr": "1",
                       "name": "rs6269442",
                       "cM": 2.0,
                       "Mb": 3.0,
                       "genotype": (-1, -1, 1, 1, 0, "U")},
                      {"chr": "1",
                       "name": "rs32285189",
                       "cM": 2.0,
                       "Mb": 3.0,
                       "genotype": (-1, "U", 1, 1, 1, -1)})},
                 {"name": "2",
                  "mb_exists": True,
                  "cm_column": 2,
                  "mb_column": 3,
                  "loci": (
                      {"chr": "2",
                       "name": "rs31443144",
                       "cM": 2.0,
                       "Mb": 3.0,
                       "genotype": (-1, -1, 1, 1, 1, -1)},
                      {"chr": "2",
                       "name": "rs6269442",
                       "cM": 2.0,
                       "Mb": 3.0,
                       "genotype": (-1, -1, 1, 1, 0, "U")})})})
