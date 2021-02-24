"""Integration tests for gemma API endpoints"""
import unittest

from dataclasses import dataclass
from typing import Callable
from unittest import mock
from gn3.app import create_app


@dataclass
class MockRedis:
    """Mock the Redis Module"""
    redis: Callable
    hget: Callable


class GemmaAPITest(unittest.TestCase):
    """Test cases for the Gemma API"""
    def setUp(self):
        self.app = create_app().test_client()

    @mock.patch("gn3.api.gemma.run_cmd")
    def test_get_version(self, mock_run_cmd):
        """Test that the correct response is returned"""
        mock_run_cmd.return_value = {"status": 0, "output": "v1.9"}
        response = self.app.get("/gemma/version", follow_redirects=True)
        self.assertEqual(response.get_json(),
                         {"status": 0, "output": "v1.9"})
        self.assertEqual(response.status_code, 200)

    @mock.patch("gn3.api.gemma.redis.Redis")
    @mock.patch("gn3.api.gemma.queue_cmd")
    @mock.patch("gn3.api.gemma.generate_gemma_computation_cmd")
    def test_run_gemma(self, mock_gemma_computation_cmd,
                       mock_queue_cmd, mock_redis):
        """Test that gemma composes the command correctly"""
        _redis_conn = MockRedis(redis=mock.MagicMock(), hget=mock.MagicMock())
        mock_redis.return_value = _redis_conn
        mock_gemma_computation_cmd.side_effect = [
            ("gemma-wrapper --json -- "
             "-g genofile.txt -p "
             "test.txt -a genofile_snps.txt "
             "-gk > /tmp/gn2/"
             "bxd_K_gUFhGu4rLG7k+CXLPk1OUg.txt"),
            ("gemma-wrapper --json -- "
             "-g genofile.txt -p "
             "test.txt -a genofile_snps.txt "
             "-gk > /tmp/gn2/"
             "bxd_GWA_gUFhGu4rLG7k+CXLPk1OUg.txt")
        ]
        mock_queue_cmd.return_value = "my-unique-id"
        response = self.app.post("/gemma/k-gwa-computation", json={
            "trait_filename": "BXD.txt",
            "geno_filename": "BXD_geno",
            "values": ["X", "N/A", "X"],
            "dataset_groupname": "BXD",
            "trait_name": "Height",
            "email": "me@me.com",
            "dataset_name": "BXD"
        })
        mock_queue_cmd.assert_has_calls(
            [mock.call(conn=_redis_conn,
                       email="me@me.com",
                       job_queue="GN3::job-queue",
                       cmd=("gemma-wrapper --json -- -g "
                            "genofile.txt -p test.txt "
                            "-a genofile_snps.txt -gk > "
                            "/tmp/gn2/bxd_K_gUFhGu4rLG7k+CXLPk1OUg.txt "
                            "&& gemma-wrapper --json -- -g "
                            "genofile.txt -p test.txt "
                            "-a genofile_snps.txt "
                            "-gk > "
                            "/tmp/gn2/"
                            "bxd_GWA_gUFhGu4rLG7k+CXLPk1OUg.txt"))]
        )
        # mock_pheno_txt_file.return_value = "/tmp/gn2/BXD_6OBEPW."
        self.assertEqual(
            response.get_json(),
            {"unique_id": 'my-unique-id',
             "status": "queued",
             "output_file": "BXD_GWA_9lo8zwOOXbfB73EcyXxAYQ.txt"})

    @mock.patch("gn3.api.gemma.redis.Redis")
    def test_check_cmd_status(self, mock_redis):
        """Test that you can check the status of a given command"""
        mock_hget = mock.MagicMock()
        mock_hget.return_value = b"test"
        _redis_conn = MockRedis(redis=mock.MagicMock(), hget=mock_hget)
        mock_redis.return_value = _redis_conn
        response = self.app.get(("/gemma/status/"
                                 "cmd%3A%3A2021-02-1217-3224-3224-1234"),
                                follow_redirects=True)
        mock_hget.assert_called_once_with(
            name="cmd::2021-02-1217-3224-3224-1234",
            key="status")
        self.assertEqual(response.get_json(),
                         {"status": "test"})
