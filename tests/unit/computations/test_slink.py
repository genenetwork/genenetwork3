"""Module contains tests for slink"""
from unittest import TestCase

from gn3.computations.slink import slink
from gn3.computations.slink import nearest
from gn3.computations.slink import LengthError
from gn3.computations.slink import MirrorError

class TestSlink(TestCase):
    """Class for testing slink functions"""

    def test_nearest_expects_list_of_lists(self):
        """Test that function only accepts a list of lists."""
        # This might be better handled with type-hints and mypy
        for item in [9, "some string", 5.432,
                     [1, 2, 3], ["test", 7.4]]:
            with self.subTest(item=item):
                with self.assertRaises(ValueError, msg="Expected list or tuple"):
                    nearest(item, 1, 1)

    def test_nearest_does_not_allow_empty_lists(self):
        """Test that function does not accept an empty list, or any of the child
        lists to be empty."""
        for lst in [[],
                    [[], []],
                    [[], [], []],
                    [[0, 1, 2], [], [1, 2, 0]]]:
            with self.subTest(lst=lst):
                with self.assertRaises(ValueError):
                    nearest(lst, 1, 1)

    def test_nearest_expects_children_are_same_length_as_parent(self):
        """Test that children lists are same length as parent list."""
        for lst in [[[0, 1]],
                    [[0, 1, 2], [3, 4, 5]],
                    [[0, 1, 2, 3], [4, 5, 6], [7, 8, 9, 0]],
                    [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9], [1, 2, 3, 4, 5], [2, 3],
                     [3, 4, 5, 6, 7]]]:
            with self.subTest(lst=lst):
                with self.assertRaises(LengthError):
                    nearest(lst, 1, 1)

    def test_nearest_expects_member_is_zero_distance_from_itself(self):
        """Test that distance of a member from itself is zero"""
        for lst in [[[1]],
                    [[1, 2], [3, 4]],
                    [1, 0, 0], [0, 0, 5], [0, 3, 4],
                    [0, 0, 0, 0], [0, 0, 3, 3], [0, 1, 2, 3], [0, 3, 2, 0]]:
            with self.subTest(lst=lst):
                with self.assertRaises(ValueError):
                    nearest(lst, 1, 1)

    def test_nearest_expects_distance_atob_is_equal_to_distance_btoa(self):
        """Test that the distance from member A to member B is the same as that
        from member B to member A."""
        for lst in [[[0, 1], [2, 0]],
                    [[0, 1, 2], [1, 0, 3], [9, 7, 0]],
                    [[0, 1, 2, 3], [7, 0, 2, 3], [2, 3, 0, 1], [8, 9, 5, 0]]]:
            with self.subTest(lst=lst):
                with self.assertRaises(MirrorError):
                    nearest(lst, 1, 1)

    def test_nearest_expects_zero_or_positive_distances(self):
        """Test that all distances are either zero, or greater than zero."""
        # Based on:
        # https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/heatmap/slink.py#L87-L89
        for lst in [[[0, -1, 2, 3], [-1, 0, 3, 4], [2, 3, 0, 5], [3, 4, 5, 0]],
                    [[0, 1, -2, 3], [1, 0, 3, 4], [-2, 3, 0, 5], [3, 4, 5, 0]],
                    [[0, 1, 2, 3], [1, 0, -3, 4], [2, -3, 0, 5], [3, 4, 5, 0]],
                    [[0, 1, 2, -3], [1, 0, 3, 4], [2, 3, 0, 5], [-3, 4, 5, 0]],
                    [[0, 1, 2, 3], [1, 0, 3, -4], [2, 3, 0, 5], [3, -4, 5, 0]],
                    [[0, 1, 2, 3], [1, 0, 3, 4], [2, 3, 0, -5], [3, 4, -5, 0]]]:
            with self.subTest(lst=lst):
                with self.assertRaises(ValueError, msg="Distances should be positive."):
                    nearest(lst, 1, 1)

    def test_nearest_returns_shortest_distance_given_coordinates_to_both_group_members(self):
        """Test that the shortest distance is returned."""
        # This test is named wrong - at least I think it is, from the expected results
        # This tests distance when both `i`, and `j` are integers
        # We still need to add tests for when (either one/both) (is/are) not (an) integer(s)
        # https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/heatmap/slink.py#L39-L40
        for lst, i, j, expected in [
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 0, 0, 0],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 0, 1, 9],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 0, 2, 3],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 0, 3, 6],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 0, 4, 11],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 1, 0, 9],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 1, 1, 0],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 1, 2, 7],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 1, 3, 5],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 1, 4, 10],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 2, 0, 3],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 2, 1, 7],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 2, 2, 0],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 2, 3, 9],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 2, 4, 2],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 3, 0, 6],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 3, 1, 5],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 3, 2, 9],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 3, 3, 0],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 3, 4, 8],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 4, 0, 11],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 4, 1, 10],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 4, 2, 2],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 4, 3, 8],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 4, 4, 0],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 0, 0, 0],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 0, 1, 9],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 0, 2, 5.5],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 0, 3, 6],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 0, 4, 11],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 1, 0, 9],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 1, 1, 0],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 1, 2, 7],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 1, 3, 5],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 1, 4, 10],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 2, 0, 5.5],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 2, 1, 7],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 2, 2, 0],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 2, 3, 9],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 2, 4, 2],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 3, 0, 6],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 3, 1, 5],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 3, 2, 9],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 3, 3, 0],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 3, 4, 3],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 4, 0, 11],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 4, 1, 10],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 4, 2, 2],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 4, 3, 3],
                [[[0, 9, 5.5, 6, 11], [9, 0, 7, 5, 10], [5.5, 7, 0, 9, 2],
                  [6, 5, 9, 0, 3], [11, 10, 2, 3, 0]],
                 4, 4, 0]]:
            with self.subTest(lst=lst):
                self.assertEqual(nearest(lst, i, j), expected)

    def test_nearest_gives_shortest_distance_between_list_of_members_and_member(self):
        """Test that the shortest distance is returned."""
        for members_distances, members_list, member_coordinate, expected_distance in [
                [[[0, 9, 3], [9, 0, 7], [3, 7, 0]], (0, 2, 3), 1, 7],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]], [0, 1, 2, 3, 4], 3, 0],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]], [0, 1, 2, 4], 3, 5],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]], [0, 2, 4], 3, 6],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]], [2, 4], 3, 9]]:
            with self.subTest(
                    members_distances=members_distances,
                    members_list=members_list,
                    member_coordinate=member_coordinate,
                    expected_distance=expected_distance):
                self.assertEqual(
                    nearest(
                        members_distances, members_list, member_coordinate),
                    expected_distance)
                self.assertEqual(
                    nearest(
                        members_distances, member_coordinate, members_list),
                    expected_distance)

    def test_nearest_returns_shortest_distance_given_two_lists_of_members(self):
        """Test that the shortest distance is returned."""
        for members_distances, members_list, member_list2, expected_distance in [
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 [0, 1, 2, 3, 4], [0, 1, 2, 3, 4], 0],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 [0, 1], [3, 4], 6],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 [0, 1], [2, 3, 4], 3],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8], [11, 10, 2, 8, 0]],
                 [0, 2], [3, 4], 6]]:
            with self.subTest(
                    members_distances=members_distances,
                    members_list=members_list,
                    member_list2=member_list2,
                    expected_distance=expected_distance):
                self.assertEqual(
                    nearest(
                        members_distances, members_list, member_list2),
                    expected_distance)
                self.assertEqual(
                    nearest(
                        members_distances, member_list2, members_list),
                    expected_distance)

    def test_slink_wrong_data_returns_empty_list(self):
        """Test that empty list is returned for wrong data."""
        for data in [1, "test", [], 2.945, nearest, [0]]:
            with self.subTest(data=data):
                self.assertEqual(slink(data), [])

    def test_slink_with_data(self):
        """Test slink with example data, and expected results for each data
        sample."""
        for data, expected in [
                [[[0, 9], [9, 0]], [0, 1, 9]],
                [[[0, 9, 3], [9, 0, 7], [3, 7, 0]], [(0, 2, 3), 1, 7]],
                [[[0, 9, 3, 6], [9, 0, 7, 5], [3, 7, 0, 9], [6, 5, 9, 0]],
                 [(0, 2, 3), (1, 3, 5), 6]],
                [[[0, 9, 3, 6, 11], [9, 0, 7, 5, 10], [3, 7, 0, 9, 2],
                  [6, 5, 9, 0, 8],
                  [11, 10, 2, 8, 0]],
                 [(0, (2, 4, 2), 3), (1, 3, 5), 6]]]:
            with self.subTest(data=data):
                self.assertEqual(slink(data), expected)
