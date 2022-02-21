"""
Test functions in gn3.data_helpers
"""

from unittest import TestCase

import pytest

from gn3.data_helpers import partition_by, partition_all, parse_csv_line

class TestDataHelpers(TestCase):
    """
    Test functions in gn3.data_helpers
    """

    @pytest.mark.unit_test
    def test_partition_all(self):
        """
        Test that `gn3.data_helpers.partition_all` partitions sequences as expected.

        Given:
            - `num`: The number of items per partition
            - `items`: A sequence of items
        When:
            - The arguments above are passed to the `gn3.data_helpers.partition_all`
        Then:
            - Return a new sequence with partitions, each of which has `num`
              items in the same order as those in `items`, save for the last
              partition which might have fewer items than `num`.
        """
        for count, items, expected in (
                (1, [0, 1, 2, 3], ((0,), (1,), (2,), (3,))),
                (3, (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
                 ((0, 1, 2), (3, 4, 5), (6, 7, 8), (9, ))),
                (4, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                 ((0, 1, 2, 3), (4, 5, 6, 7), (8, 9))),
                (13, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                 ((0, 1, 2, 3, 4, 5, 6, 7, 8, 9), ))):
            with self.subTest(n=count, items=items):
                self.assertEqual(tuple(partition_all(count, items)), expected)

    @pytest.mark.unit_test
    def test_parse_csv_line(self):
        """
        Test parsing a single line from a CSV file

        Given:
            - `line`: a line read from a csv file
            - `delimiter`: the expected delimiter in the csv file
            - `quoting`: the quoting enclosing each column in the csv file
        When:
            - `line` is parsed with the `parse_csv_file` with the given
               parameters
        Then:
            - return a tuple of the columns in the CSV file, without the
              delimiter and quoting
        """
        for line, delimiter, quoting, expected in (
                ('"this","is","a","test"', ",", '"', ("this", "is", "a", "test")),
                ('"this","is","a","test"', ",", None, ('"this"', '"is"', '"a"', '"test"'))):
            with self.subTest(line=line, delimiter=delimiter, quoting=quoting):
                self.assertEqual(
                    parse_csv_line(
                        line=line, delimiter=delimiter, quoting=quoting),
                    expected)

    @pytest.mark.unit_test
    def test_partition_by(self):
        """
        Test that `partition_by` groups the data using the given predicate

        Given:
          - `part_fn`: a predicate funtion that return boolean True/False
          - `items`: a sequence of items
        When:
          - the partitioning predicate function and the sequence of items are
            passed to the `partition_by` function
        Then:
          - the result is a tuple, with sub-tuples containing the data in the
            original sequence. Each sub-tuple is a partition, ending as soon as
            the next value in the sequence, when passed to `part_fn`, returns
            boolean `True`.
        """
        for part_fn, items, expected in (
                (lambda s: s.startswith("----"),
                 ("------", "a", "b", "-----", "c", "----", "d", "e", "---",
                  "f"),
                 (("------", "a", "b"), ("-----", "c"),
                  ("----", "d", "e", "---", "f"))),
                (lambda x: (x % 2) == 0,
                 (0, 1, 3, 2, 4, 5, 7, 6, 9, 1),
                 ((0, 1, 3), (2,), (4, 5, 7), (6, 9, 1))),):
            with self.subTest(items=items):
                self.assertEqual(partition_by(part_fn, items), expected)
