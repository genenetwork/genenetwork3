# pylint: disable=R0913
"""Integration tests for gemma API endpoints"""
import os
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
        self.app = create_app({
            "GENODIR":
            os.path.abspath(
                os.path.join(os.path.dirname(__file__), "test_data/")),
            "REDIS_JOB_QUEUE":
            "GN3::job-queue",
            "GEMMA_WRAPPER_CMD":
            "gemma-wrapper"
        }).test_client()

    @mock.patch("gn3.api.gemma.run_cmd")
    def test_get_version(self, mock_run_cmd):
        """Test that the correct response is returned"""
        mock_run_cmd.return_value = {"status": 0, "output": "v1.9"}
        response = self.app.get("/api/gemma/version", follow_redirects=True)
        self.assertEqual(response.get_json(), {"status": 0, "output": "v1.9"})
        self.assertEqual(response.status_code, 200)

    @mock.patch("gn3.api.gemma.redis.Redis")
    def test_check_cmd_status(self, mock_redis):
        """Test that you can check the status of a given command"""
        mock_hget = mock.MagicMock()
        mock_hget.return_value = b"test"
        _redis_conn = MockRedis(redis=mock.MagicMock(), hget=mock_hget)
        mock_redis.return_value = _redis_conn
        response = self.app.get(("/api/gemma/status/"
                                 "cmd%3A%3A2021-02-1217-3224-3224-1234"),
                                follow_redirects=True)
        mock_hget.assert_called_once_with(
            name="cmd::2021-02-1217-3224-3224-1234", key="status")
        self.assertEqual(response.get_json(), {"status": "test"})

    @mock.patch("gn3.api.gemma.queue_cmd")
    @mock.patch("gn3.computations.gemma.get_hash_of_files")
    @mock.patch("gn3.api.gemma.jsonfile_to_dict")
    @mock.patch("gn3.api.gemma.do_paths_exist")
    @mock.patch("gn3.api.gemma.redis.Redis")
    @mock.patch("gn3.api.gemma.cache_ipfs_file")
    def test_k_compute(self, mock_ipfs_cache,
                       mock_redis,
                       mock_path_exist, mock_json, mock_hash,
                       mock_queue_cmd):
        """Test /gemma/k-compute/<token>"""
        mock_ipfs_cache.return_value = ("/tmp/cache/"
                                        "QmQPeNsJPyVWPFDVHb"
                                        "77w8G42Fvo15z4bG2X8D2GhfbSXc/"
                                        "genotype.txt")
        mock_path_exist.return_value, _redis_conn = True, mock.MagicMock()
        mock_redis.return_value = _redis_conn
        mock_queue_cmd.return_value = "my-unique-id"
        mock_json.return_value = {
            "geno": "genofile.txt",
            "pheno": "phenofile.txt",
            "snps": "snpfile.txt",
        }
        mock_hash.return_value = "hash"
        response = self.app.post("/api/gemma/k-compute/test-data")
        mock_queue_cmd.assert_called_once_with(
            conn=_redis_conn,
            email=None,
            job_queue='GN3::job-queue',
            cmd=("gemma-wrapper --json -- "
                 "-g /tmp/cache/QmQPeNsJPyVWPFD"
                 "VHb77w8G42Fvo15z4bG2X8D2GhfbSXc/genotype.txt "
                 "-p /tmp/test-data/phenofile.txt "
                 "-a /tmp/test-data/snpfile.txt "
                 "-gk > /tmp/test-data/hash-output.json"))
        self.assertEqual(
            response.get_json(), {
                "output_file": "hash-output.json",
                "status": "queued",
                "unique_id": "my-unique-id"
            })

    @mock.patch("gn3.api.gemma.queue_cmd")
    @mock.patch("gn3.computations.gemma.get_hash_of_files")
    @mock.patch("gn3.api.gemma.jsonfile_to_dict")
    @mock.patch("gn3.api.gemma.do_paths_exist")
    @mock.patch("gn3.api.gemma.redis.Redis")
    @mock.patch("gn3.api.gemma.cache_ipfs_file")
    def test_k_compute_loco(self, mock_ipfs_cache,
                            mock_redis, mock_path_exist, mock_json,
                            mock_hash, mock_queue_cmd):
        """Test /gemma/k-compute/loco/<chromosomes>/<token>"""
        mock_ipfs_cache.return_value = ("/tmp/cache/"
                                        "QmQPeNsJPyVWPFDVHb"
                                        "77w8G42Fvo15z4bG2X8D2GhfbSXc/"
                                        "genotype.txt")
        mock_path_exist.return_value, _redis_conn = True, mock.MagicMock()
        mock_redis.return_value = _redis_conn
        mock_queue_cmd.return_value = "my-unique-id"
        mock_json.return_value = {
            "geno": "genofile.txt",
            "pheno": "phenofile.txt",
            "snps": "snpfile.txt",
        }
        mock_hash.return_value = "hash"
        response = self.app.post(("/api/gemma/k-compute/loco/"
                                  "1%2C2%2C3%2C4%2C5%2C6/test-data"))
        mock_queue_cmd.assert_called_once_with(
            conn=_redis_conn,
            email=None,
            job_queue='GN3::job-queue',
            cmd=("gemma-wrapper --json --loco "
                 "1,2,3,4,5,6 -- "
                 "-g /tmp/cache/QmQPeNsJPyVWPFD"
                 "VHb77w8G42Fvo15z4bG2X8D2GhfbSXc/genotype.txt "
                 "-p /tmp/test-data/phenofile.txt "
                 "-a /tmp/test-data/snpfile.txt "
                 "-gk > /tmp/test-data/hash-3R77Mz-output.json"))
        self.assertEqual(
            response.get_json(), {
                "output_file": "hash-3R77Mz-output.json",
                "status": "queued",
                "unique_id": "my-unique-id"
            })

    @mock.patch("gn3.api.gemma.queue_cmd")
    @mock.patch("gn3.computations.gemma.get_hash_of_files")
    @mock.patch("gn3.api.gemma.jsonfile_to_dict")
    @mock.patch("gn3.api.gemma.do_paths_exist")
    @mock.patch("gn3.api.gemma.redis.Redis")
    @mock.patch("gn3.api.gemma.cache_ipfs_file")
    def test_gwa_compute(self, mock_ipfs_cache,
                         mock_redis, mock_path_exist, mock_json,
                         mock_hash, mock_queue_cmd):
        """Test /gemma/gwa-compute/<k-inputfile>/<token>"""
        mock_ipfs_cache.return_value = ("/tmp/cache/"
                                        "QmQPeNsJPyVWPFDVHb"
                                        "77w8G42Fvo15z4bG2X8D2GhfbSXc/"
                                        "genotype.txt")
        mock_path_exist.return_value, _redis_conn = True, mock.MagicMock()
        mock_redis.return_value = _redis_conn
        mock_queue_cmd.return_value = "my-unique-id"
        mock_json.return_value = {
            "geno": "genofile.txt",
            "pheno": "phenofile.txt",
            "snps": "snpfile.txt",
        }
        mock_hash.return_value = "hash"
        response = self.app.post(("/api/gemma/gwa-compute/hash-k-output.json/"
                                  "my-token"))
        mock_hash.assert_called_once_with([
            ('/tmp/cache/QmQPeNsJPyVWPFDVHb77w8'
             'G42Fvo15z4bG2X8D2GhfbSXc/genotype.txt'),
            '/tmp/my-token/phenofile.txt',
            '/tmp/my-token/snpfile.txt'
        ])
        mock_queue_cmd.assert_called_once_with(
            conn=_redis_conn,
            email=None,
            job_queue='GN3::job-queue',
            cmd=("gemma-wrapper --json "
                 "--input /tmp/my-token/hash-k-output.json"
                 " -- "
                 "-g /tmp/cache/QmQPeNsJPyVWPFD"
                 "VHb77w8G42Fvo15z4bG2X8D2GhfbSXc/genotype.txt "
                 "-p /tmp/my-token/phenofile.txt "
                 "-a /tmp/my-token/snpfile.txt "
                 "-lmm 9 -gk > /tmp/my-token/hash-output.json"))
        self.assertEqual(
            response.get_json(), {
                "unique_id": "my-unique-id",
                "status": "queued",
                "output_file": "hash-output.json"
            })

    @mock.patch("gn3.api.gemma.queue_cmd")
    @mock.patch("gn3.computations.gemma.get_hash_of_files")
    @mock.patch("gn3.api.gemma.jsonfile_to_dict")
    @mock.patch("gn3.api.gemma.do_paths_exist")
    @mock.patch("gn3.api.gemma.redis.Redis")
    @mock.patch("gn3.api.gemma.cache_ipfs_file")
    def test_gwa_compute_with_covars(self, mock_ipfs_cache,
                                     mock_redis, mock_path_exist,
                                     mock_json, mock_hash, mock_queue_cmd):
        """Test /gemma/gwa-compute/covars/<k-inputfile>/<token>"""
        mock_ipfs_cache.return_value = ("/tmp/cache/"
                                        "QmQPeNsJPyVWPFDVHb"
                                        "77w8G42Fvo15z4bG2X8D2GhfbSXc/"
                                        "genotype.txt")
        mock_path_exist.return_value, _redis_conn = True, mock.MagicMock()
        mock_redis.return_value = _redis_conn
        mock_queue_cmd.return_value = "my-unique-id"
        mock_path_exist.return_value = True
        mock_json.return_value = {
            "geno": "genofile.txt",
            "pheno": "phenofile.txt",
            "snps": "snpfile.txt",
            "covar": "covarfile.txt",
        }
        mock_hash.return_value = "hash"
        response = self.app.post(("/api/gemma/gwa-compute/"
                                  "covars/hash-k-output.json/"
                                  "my-token"))
        mock_hash.assert_called_once_with([
            ('/tmp/cache/QmQPeNsJPyVWPFDVHb77w8'
             'G42Fvo15z4bG2X8D2GhfbSXc/genotype.txt'),
            '/tmp/my-token/phenofile.txt',
            '/tmp/my-token/snpfile.txt', '/tmp/my-token/covarfile.txt'
        ])
        mock_queue_cmd.assert_called_once_with(
            conn=_redis_conn,
            email=None,
            job_queue="GN3::job-queue",
            cmd=("gemma-wrapper --json --input "
                 "/tmp/my-token/hash-k-output.json -- "
                 "-g /tmp/cache/QmQPeNsJPyVWPFD"
                 "VHb77w8G42Fvo15z4bG2X8D2GhfbSXc/genotype.txt "
                 "-p /tmp/my-token/phenofile.txt "
                 "-a /tmp/my-token/snpfile.txt "
                 "-c /tmp/my-token/covarfile.txt -lmm 9 "
                 "-gk > /tmp/my-token/hash-output.json"))
        self.assertEqual(
            response.get_json(), {
                "unique_id": "my-unique-id",
                "status": "queued",
                "output_file": "hash-output.json"
            })

    @mock.patch("gn3.api.gemma.queue_cmd")
    @mock.patch("gn3.computations.gemma.get_hash_of_files")
    @mock.patch("gn3.api.gemma.jsonfile_to_dict")
    @mock.patch("gn3.api.gemma.do_paths_exist")
    @mock.patch("gn3.api.gemma.redis.Redis")
    @mock.patch("gn3.api.gemma.cache_ipfs_file")
    def test_gwa_compute_with_loco_only(self, mock_ipfs_cache,
                                        mock_redis, mock_path_exist,
                                        mock_json, mock_hash, mock_queue_cmd):
        """Test /gemma/gwa-compute/<k-inputfile>/loco/maf/<maf>/<token>

        """
        mock_ipfs_cache.return_value = ("/tmp/cache/"
                                        "QmQPeNsJPyVWPFDVHb"
                                        "77w8G42Fvo15z4bG2X8D2GhfbSXc/"
                                        "genotype.txt")
        mock_path_exist.return_value, _redis_conn = True, mock.MagicMock()
        mock_redis.return_value = _redis_conn
        mock_queue_cmd.return_value = "my-unique-id"
        mock_json.return_value = {
            "pheno": "phenofile.txt",
            "snps": "snpfile.txt",
        }
        mock_hash.return_value = "hash"
        response = self.app.post(("/api/gemma/gwa-compute/"
                                  "hash-output.json/loco/"
                                  "maf/21/my-token"))
        mock_hash.assert_called_once_with([
            ('/tmp/cache/QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc/'
             'genotype.txt'),
            '/tmp/my-token/phenofile.txt',
            '/tmp/my-token/snpfile.txt'
        ])
        mock_queue_cmd.assert_called_once_with(
            conn=_redis_conn,
            email=None,
            job_queue='GN3::job-queue',
            cmd=("gemma-wrapper --json --loco --input "
                 "/tmp/my-token/hash-output.json -- "
                 "-g /tmp/cache/QmQPeNsJPyVWPFD"
                 "VHb77w8G42Fvo15z4bG2X8D2GhfbSXc/genotype.txt "
                 "-p /tmp/my-token/phenofile.txt "
                 "-a /tmp/my-token/snpfile.txt "
                 "-lmm 9 -maf 21.0 "
                 "-gk > /tmp/my-token/hash-output.json"))
        self.assertEqual(
            response.get_json(), {
                "unique_id": "my-unique-id",
                "status": "queued",
                "output_file": "hash-output.json"
            })

    @mock.patch("gn3.api.gemma.queue_cmd")
    @mock.patch("gn3.computations.gemma.get_hash_of_files")
    @mock.patch("gn3.api.gemma.jsonfile_to_dict")
    @mock.patch("gn3.api.gemma.do_paths_exist")
    @mock.patch("gn3.api.gemma.redis.Redis")
    @mock.patch("gn3.api.gemma.cache_ipfs_file")
    def test_gwa_compute_with_loco_covars(self, mock_ipfs_cache,
                                          mock_redis, mock_path_exist,
                                          mock_json, mock_hash,
                                          mock_queue_cmd):
        """Test /gemma/gwa-compute/<k-inputfile>/loco/covars/maf/<maf>/<token>

        """
        mock_ipfs_cache.return_value = ("/tmp/cache/"
                                        "QmQPeNsJPyVWPFDVHb"
                                        "77w8G42Fvo15z4bG2X8D2GhfbSXc/"
                                        "genotype.txt")
        mock_path_exist.return_value, _redis_conn = True, mock.MagicMock()
        mock_redis.return_value = _redis_conn
        mock_queue_cmd.return_value = "my-unique-id"
        mock_json.return_value = {
            "pheno": "phenofile.txt",
            "snps": "snpfile.txt",
            "covar": "covarfile.txt",
        }
        mock_hash.return_value = "hash"
        response = self.app.post(("/api/gemma/gwa-compute/"
                                  "hash-output.json/loco/"
                                  "covars/maf/21/my-token"))
        mock_hash.assert_called_once_with([
            ('/tmp/cache/QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc/'
             'genotype.txt'), '/tmp/my-token/phenofile.txt',
            '/tmp/my-token/snpfile.txt', "/tmp/my-token/covarfile.txt"
        ])
        mock_queue_cmd.assert_called_once_with(
            conn=_redis_conn,
            email=None,
            job_queue='GN3::job-queue',
            cmd=("gemma-wrapper --json --loco --input "
                 "/tmp/my-token/hash-output.json -- "
                 "-g /tmp/cache/QmQPeNsJPyVWPFD"
                 "VHb77w8G42Fvo15z4bG2X8D2GhfbSXc/genotype.txt "
                 "-p /tmp/my-token/phenofile.txt "
                 "-a /tmp/my-token/snpfile.txt "
                 "-c /tmp/my-token/covarfile.txt "
                 "-lmm 9 -maf 21.0 "
                 "-gk > /tmp/my-token/hash-output.json"))
        self.assertEqual(
            response.get_json(), {
                "unique_id": "my-unique-id",
                "status": "queued",
                "output_file": "hash-output.json"
            })

    @mock.patch("gn3.api.gemma.queue_cmd")
    @mock.patch("gn3.computations.gemma.get_hash_of_files")
    @mock.patch("gn3.api.gemma.jsonfile_to_dict")
    @mock.patch("gn3.api.gemma.do_paths_exist")
    @mock.patch("gn3.api.gemma.redis.Redis")
    @mock.patch("gn3.api.gemma.cache_ipfs_file")
    def test_k_gwa_compute_without_loco_covars(self, mock_ipfs_cache,
                                               mock_redis,
                                               mock_path_exist, mock_json,
                                               mock_hash, mock_queue_cmd):
        """Test /gemma/k-gwa-compute/<token>

        """
        mock_ipfs_cache.return_value = ("/tmp/cache/"
                                        "QmQPeNsJPyVWPFDVHb"
                                        "77w8G42Fvo15z4bG2X8D2GhfbSXc/"
                                        "genotype.txt")
        mock_path_exist.return_value, _redis_conn = True, mock.MagicMock()
        mock_redis.return_value = _redis_conn
        mock_queue_cmd.return_value = "my-unique-id"
        mock_json.return_value = {
            "pheno": "phenofile.txt",
            "snps": "snpfile.txt",
        }
        mock_hash.return_value = "hash"
        response = self.app.post(("/api/gemma/k-gwa-compute/" "my-token"))
        mock_hash.assert_called_with([
            ('/tmp/cache/QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc/'
             'genotype.txt'), '/tmp/my-token/phenofile.txt',
            '/tmp/my-token/snpfile.txt'
        ])
        mock_queue_cmd.assert_called_once_with(
            conn=_redis_conn,
            email=None,
            job_queue='GN3::job-queue',
            cmd=("gemma-wrapper --json -- "
                 "-g /tmp/cache/QmQPeNsJPyVWPFD"
                 "VHb77w8G42Fvo15z4bG2X8D2GhfbSXc/genotype.txt "
                 "-p /tmp/my-token/phenofile.txt "
                 "-a /tmp/my-token/snpfile.txt "
                 "-gk > /tmp/my-token/hash-output.json "
                 "&& gemma-wrapper --json "
                 "--input /tmp/my-token/hash-output.json -- "
                 "-g /tmp/cache/QmQPeNsJPyVWPFD"
                 "VHb77w8G42Fvo15z4bG2X8D2GhfbSXc/genotype.txt "
                 "-p /tmp/my-token/phenofile.txt "
                 "-a /tmp/my-token/snpfile.txt -lmm 9 "
                 "-gk > /tmp/my-token/hash-output.json"))
        self.assertEqual(
            response.get_json(), {
                "unique_id": "my-unique-id",
                "status": "queued",
                "output_file": "hash-output.json"
            })

    @mock.patch("gn3.api.gemma.queue_cmd")
    @mock.patch("gn3.computations.gemma.get_hash_of_files")
    @mock.patch("gn3.api.gemma.jsonfile_to_dict")
    @mock.patch("gn3.api.gemma.do_paths_exist")
    @mock.patch("gn3.api.gemma.redis.Redis")
    @mock.patch("gn3.api.gemma.cache_ipfs_file")
    def test_k_gwa_compute_with_covars_only(self, mock_ipfs_cache,
                                            mock_redis, mock_path_exist,
                                            mock_json, mock_hash,
                                            mock_queue_cmd):
        """Test /gemma/k-gwa-compute/covars/<token>

        """
        mock_ipfs_cache.return_value = ("/tmp/cache/"
                                        "QmQPeNsJPyVWPFDVHb"
                                        "77w8G42Fvo15z4bG2X8D2GhfbSXc/"
                                        "genotype.txt")
        mock_path_exist.return_value, _redis_conn = True, mock.MagicMock()
        mock_redis.return_value = _redis_conn
        mock_queue_cmd.return_value = "my-unique-id"
        mock_json.return_value = {
            "pheno": "phenofile.txt",
            "snps": "snpfile.txt",
            "covar": "covarfile.txt",
        }
        mock_hash.return_value = "hash"
        response = self.app.post("/api/gemma/k-gwa-compute/covars/my-token")
        mock_hash.assert_has_calls([
            mock.call([
                ('/tmp/cache/QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc/'
                 'genotype.txt'), '/tmp/my-token/phenofile.txt',
                '/tmp/my-token/snpfile.txt'
            ]),
            mock.call([
                ('/tmp/cache/QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc/'
                 'genotype.txt'), '/tmp/my-token/phenofile.txt',
                '/tmp/my-token/snpfile.txt', "/tmp/my-token/covarfile.txt"
            ])
        ])
        mock_queue_cmd.assert_called_once_with(
            conn=_redis_conn,
            email=None,
            job_queue='GN3::job-queue',
            cmd=("gemma-wrapper --json -- "
                 "-g /tmp/cache/QmQPeNsJPyVWPFD"
                 "VHb77w8G42Fvo15z4bG2X8D2GhfbSXc/genotype.txt "
                 "-p /tmp/my-token/phenofile.txt "
                 "-a /tmp/my-token/snpfile.txt "
                 "-gk > /tmp/my-token/hash-output.json "
                 "&& gemma-wrapper --json "
                 "--input /tmp/my-token/hash-output.json -- "
                 "-g /tmp/cache/QmQPeNsJPyVWPFD"
                 "VHb77w8G42Fvo15z4bG2X8D2GhfbSXc/genotype.txt "
                 "-p /tmp/my-token/phenofile.txt "
                 "-a /tmp/my-token/snpfile.txt "
                 "-c /tmp/my-token/covarfile.txt -lmm 9 "
                 "-gk > /tmp/my-token/hash-output.json"))
        self.assertEqual(
            response.get_json(), {
                "unique_id": "my-unique-id",
                "status": "queued",
                "output_file": "hash-output.json"
            })

    @mock.patch("gn3.api.gemma.queue_cmd")
    @mock.patch("gn3.computations.gemma.get_hash_of_files")
    @mock.patch("gn3.api.gemma.jsonfile_to_dict")
    @mock.patch("gn3.api.gemma.do_paths_exist")
    @mock.patch("gn3.api.gemma.redis.Redis")
    @mock.patch("gn3.api.gemma.cache_ipfs_file")
    def test_k_gwa_compute_with_loco_only(self, mock_ipfs_cache,
                                          mock_redis, mock_path_exist,
                                          mock_json, mock_hash,
                                          mock_queue_cmd):
        """Test /gemma/k-gwa-compute/loco/<chromosomes>/maf/<maf>/<token>

        """
        mock_ipfs_cache.return_value = ("/tmp/cache/"
                                        "QmQPeNsJPyVWPFDVHb"
                                        "77w8G42Fvo15z4bG2X8D2GhfbSXc/"
                                        "genotype.txt")
        mock_path_exist.return_value, _redis_conn = True, mock.MagicMock()
        mock_redis.return_value = _redis_conn
        mock_queue_cmd.return_value = "my-unique-id"
        mock_json.return_value = {
            "pheno": "phenofile.txt",
            "snps": "snpfile.txt",
        }
        mock_hash.return_value = "hash"
        response = self.app.post(
            "/api/gemma/k-gwa-compute/loco/1%2C2%2C3%2C4/maf/9/my-token")
        mock_hash.assert_has_calls([
            mock.call([
                ('/tmp/cache/QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc/'
                 'genotype.txt'),
                '/tmp/my-token/phenofile.txt',
                '/tmp/my-token/snpfile.txt'
            ]),
            mock.call([
                ('/tmp/cache/QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc/'
                 'genotype.txt'),
                '/tmp/my-token/phenofile.txt',
                '/tmp/my-token/snpfile.txt'
            ]),
        ])
        mock_queue_cmd.assert_called_once_with(
            conn=_redis_conn,
            email=None,
            job_queue='GN3::job-queue',
            cmd=("gemma-wrapper --json --loco 1,2,3,4 -- "
                 "-g /tmp/cache/QmQPeNsJPyVWPFD"
                 "VHb77w8G42Fvo15z4bG2X8D2GhfbSXc/genotype.txt "
                 "-p /tmp/my-token/phenofile.txt "
                 "-a /tmp/my-token/snpfile.txt "
                 "-gk > /tmp/my-token/hash-+O9bus-output.json "
                 "&& gemma-wrapper --json --loco "
                 "--input /tmp/my-token/hash-+O9bus-output.json -- "
                 "-g /tmp/cache/QmQPeNsJPyVWPFD"
                 "VHb77w8G42Fvo15z4bG2X8D2GhfbSXc/genotype.txt "
                 "-p /tmp/my-token/phenofile.txt "
                 "-a /tmp/my-token/snpfile.txt -maf 9.0 -lmm 9 "
                 "-gk > /tmp/my-token/hash-output.json"))
        self.assertEqual(
            response.get_json(), {
                "unique_id": "my-unique-id",
                "status": "queued",
                "output_file": "hash-output.json"
            })

    @mock.patch("gn3.api.gemma.queue_cmd")
    @mock.patch("gn3.computations.gemma.get_hash_of_files")
    @mock.patch("gn3.api.gemma.jsonfile_to_dict")
    @mock.patch("gn3.api.gemma.do_paths_exist")
    @mock.patch("gn3.api.gemma.redis.Redis")
    @mock.patch("gn3.api.gemma.cache_ipfs_file")
    def test_k_gwa_compute_with_loco_and_covar(self, mock_ipfs_cache,
                                               mock_redis,
                                               mock_path_exist, mock_json,
                                               mock_hash, mock_queue_cmd):
        """Test /k-gwa-compute/covars/loco/<chromosomes>/maf/<maf>/<token>

        """
        mock_ipfs_cache.return_value = ("/tmp/cache/"
                                        "QmQPeNsJPyVWPFDVHb"
                                        "77w8G42Fvo15z4bG2X8D2GhfbSXc/"
                                        "genotype.txt")
        mock_path_exist.return_value, _redis_conn = True, mock.MagicMock()
        mock_redis.return_value = _redis_conn
        mock_queue_cmd.return_value = "my-unique-id"
        mock_json.return_value = {
            "pheno": "phenofile.txt",
            "snps": "snpfile.txt",
            "covar": "covarfile.txt",
        }
        mock_hash.return_value = "hash"
        response = self.app.post(("/api/gemma/k-gwa-compute/covars/"
                                  "loco/1%2C2%2C3%2C4/maf/9/my-token"))
        mock_hash.assert_has_calls([
            mock.call([
                ('/tmp/cache/QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc/'
                 'genotype.txt'),
                '/tmp/my-token/phenofile.txt',
                '/tmp/my-token/snpfile.txt'
            ]),
            mock.call([
                ('/tmp/cache/QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc/'
                 'genotype.txt'),
                '/tmp/my-token/phenofile.txt',
                '/tmp/my-token/snpfile.txt', '/tmp/my-token/covarfile.txt'
            ]),
        ])
        mock_queue_cmd.assert_called_once_with(
            conn=_redis_conn,
            email=None,
            job_queue='GN3::job-queue',
            cmd=("gemma-wrapper --json --loco 1,2,3,4 -- "
                 "-g /tmp/cache/QmQPeNsJPyVWPFD"
                 "VHb77w8G42Fvo15z4bG2X8D2GhfbSXc/genotype.txt "
                 "-p /tmp/my-token/phenofile.txt "
                 "-a /tmp/my-token/snpfile.txt "
                 "-gk > /tmp/my-token/hash-+O9bus-output.json "
                 "&& gemma-wrapper --json --loco "
                 "--input /tmp/my-token/hash-+O9bus-output.json -- "
                 "-g /tmp/cache/QmQPeNsJPyVWPFD"
                 "VHb77w8G42Fvo15z4bG2X8D2GhfbSXc/genotype.txt "
                 "-p /tmp/my-token/phenofile.txt "
                 "-a /tmp/my-token/snpfile.txt "
                 "-c /tmp/my-token/covarfile.txt -maf 9.0 -lmm 9 "
                 "-gk > /tmp/my-token/hash-output.json"))
        self.assertEqual(
            response.get_json(), {
                "unique_id": "my-unique-id",
                "status": "queued",
                "output_file": "hash-output.json"
            })
