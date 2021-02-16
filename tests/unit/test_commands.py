"""Test cases for procedures defined in commands.py"""
import os
import unittest

from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from unittest import mock
from gn3.commands import compose_gemma_cmd
from gn3.commands import queue_cmd
from gn3.commands import run_cmd
from gn3.exceptions import RedisConnectionError


@dataclass
class MockRedis:
    """Mock Redis connection"""
    ping: Callable
    hset: mock.MagicMock
    rpush: mock.MagicMock


class TestCommands(unittest.TestCase):
    """Test cases for commands.py"""

    @mock.patch("gn3.commands.lookup_file")
    def test_compose_gemma_cmd_no_extra_args(self, mock_lookup_file):
        """Test that thhe gemma cmd is composed correctly"""
        metadata_file = os.path.join(os.path.dirname(__file__),
                                     "test_data/metadata.json")
        mock_lookup_file.side_effect = [metadata_file,
                                        "/tmp/genofile.txt",
                                        "/tmp/gf13Ad0tRX/phenofile.txt"]
        self.assertEqual(compose_gemma_cmd("gf13Ad0t",
                                           "metadata.json",
                                           gemma_wrapper_cmd="gemma-wrapper",
                                           gemma_wrapper_kwargs=None,
                                           gemma_kwargs=None,
                                           gemma_args=["-gk"]),
                         ("gemma-wrapper --json -- "
                          "-g /tmp/genofile.txt "
                          "-p /tmp/gf13Ad0tRX/phenofile.txt"
                          " -gk"))

    def test_queue_cmd_exception_raised_when_redis_is_down(self):
        """Test that the correct error is raised when Redis is unavailable"""
        self.assertRaises(RedisConnectionError,
                          queue_cmd,
                          cmd="ls",
                          conn=MockRedis(ping=lambda: False,
                                         hset=mock.MagicMock(),
                                         rpush=mock.MagicMock()))

    @mock.patch("gn3.commands.datetime")
    @mock.patch("gn3.commands.uuid4")
    def test_queue_cmd_correct_calls_to_redis(self, mock_uuid4,
                                              mock_datetime):
        """Test that the cmd is queued properly"""
        mock_uuid4.return_value = 1234
        mock_datetime.now.return_value = datetime.fromisoformat('2021-02-12 '
                                                                '17:32:24.'
                                                                '859097')
        mock_redis_conn = MockRedis(ping=lambda: True,
                                    hset=mock.MagicMock(),
                                    rpush=mock.MagicMock())
        actual_unique_id = "cmd::2021-02-1217-3224-3224-1234"
        self.assertEqual(queue_cmd(cmd="ls",
                                   conn=mock_redis_conn),
                         actual_unique_id)
        mock_redis_conn.hset.assert_has_calls(
            [mock.call("cmd", "ls", actual_unique_id),
             mock.call("result", "", actual_unique_id),
             mock.call("status", "queued", actual_unique_id)])
        mock_redis_conn.rpush.assert_has_calls(
            [mock.call("GN2::job-queue", actual_unique_id)])

    @mock.patch("gn3.commands.datetime")
    @mock.patch("gn3.commands.uuid4")
    def test_queue_cmd_right_calls_to_redis_with_email(self,
                                                       mock_uuid4,
                                                       mock_datetime):
        """Test that the cmd is queued properly when given the email"""
        mock_uuid4.return_value = 1234
        mock_datetime.now.return_value = datetime.fromisoformat('2021-02-12 '
                                                                '17:32:24.'
                                                                '859097')
        mock_redis_conn = MockRedis(ping=lambda: True,
                                    hset=mock.MagicMock(),
                                    rpush=mock.MagicMock())
        actual_unique_id = "cmd::2021-02-1217-3224-3224-1234"
        self.assertEqual(queue_cmd(cmd="ls",
                                   conn=mock_redis_conn,
                                   email="me@me.com"),
                         actual_unique_id)
        mock_redis_conn.hset.assert_has_calls(
            [mock.call("cmd", "ls", actual_unique_id),
             mock.call("result", "", actual_unique_id),
             mock.call("status", "queued", actual_unique_id),
             mock.call("email", "me@me.com", actual_unique_id)])
        mock_redis_conn.rpush.assert_has_calls(
            [mock.call("GN2::job-queue", actual_unique_id)])

    def test_run_cmd_correct_input(self):
        """Test that a correct cmd is processed correctly"""
        self.assertEqual(run_cmd("echo test"),
                         {"code": 0, "output": "test\n"})

    def test_run_cmd_incorrect_input(self):
        """Test that an incorrect cmd is processed correctly"""
        result = run_cmd("echoo test")
        self.assertEqual(127, result.get("code"))
