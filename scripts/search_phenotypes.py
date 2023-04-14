"""
A script to do search for phenotype traits using the Xapian Search endpoint.
"""
import uuid
import json
import traceback
from urllib.parse import urljoin
from typing import Any, Iterable
from datetime import datetime, timedelta

import click
import redis
import requests

from gn3.auth import db as authdb
from gn3 import db_utils as gn3db
from gn3.settings import SQL_URI, AUTH_DB
from gn3.auth.authorisation.data.phenotypes import linked_phenotype_data

class NoSearchResults(Exception):
    """Raise when there are no results for a search."""

def do_search(
        host: str, query: str, per_page: int, page: int = 1) -> Iterable[dict[str, Any]]:
    """Do the search and return the results"""
    search_uri = urljoin(host, (f"search/?page={page}&per_page={per_page}"
                                f"&type=phenotype&query={query}"))
    response = requests.get(search_uri)
    results = response.json()
    if len(results) > 0:
        return (item for item in results)
    raise NoSearchResults(f"No results for search '{query}'")

def __filter_object__(search_item):
    return (search_item["species"], search_item["group"],
            search_item["dataset"], search_item["name"])

def remove_selected(search_results, selected: tuple):
    """Remove any item that the user has selected."""
    return (item for item in search_results if __filter_object__(item) not in selected)

def remove_linked(search_results, linked: tuple):
    """Remove any item that has been already linked to a user group."""
    return (item for item in search_results if __filter_object__(item) not in linked)

def save_to_redis(redisconn: redis.Redis, redisname: str, results: tuple[dict[str, Any], ...]):
    """Save the results to redis db."""
    key = "search_results"
    prev_results = tuple(json.loads(redisconn.hget(redisname, key) or "[]"))
    redisconn.hset(redisname, key, json.dumps(prev_results + results))

def expire_redis_results(redisconn: redis.Redis, redisname: str):
    """Expire the results after a while to ensure they are cleaned up."""
    redisconn.expireat(redisname, datetime.now() + timedelta(minutes=30))

@click.command()
@click.argument("species")
@click.argument("query")
@click.argument("job-id", type=click.UUID)
@click.option(
    "--host", default="http://localhost:8080/api/", help="The URI to GN3.")
@click.option("--per-page", default=10000, help="Number of results per page.")
@click.option("--selected", default="[]", help="Selected traits.")
@click.option(
    "--auth-db-uri", default=AUTH_DB, help="The SQL URI to the auth database.")
@click.option(
    "--gn3-db-uri", default=SQL_URI,
    help="The SQL URI to the main GN3 database.")
@click.option(
    "--redis-uri", default="redis://:@localhost:6379/0",
    help="The URI to the redis server.")
def search(# pylint: disable=[too-many-arguments, too-many-locals]
        species: str, query: str, job_id: uuid.UUID, host: str, per_page: int,
        selected: str, auth_db_uri: str, gn3_db_uri: str, redis_uri: str):
    """
    Search for phenotype traits, filtering out any linked and selected traits,
    loading more and more pages until the `per_page` quota is fulfilled or the
    search runs out of pages.
    """
    redisname = f"GN3:JOBS:{job_id}"
    with (authdb.connection(auth_db_uri) as authconn,
          gn3db.database_connection(gn3_db_uri) as gn3conn,
          redis.Redis.from_url(redis_uri, decode_responses=True) as redisconn):
        redisconn.hset(redisname, "status", "started")
        save_to_redis(redisconn, redisname, tuple())
        try:
            search_query = f"species:{species}" + (
                f" AND ({query})" if bool(query) else "")
            filter_keys = ("SpeciesName", "InbredSetName", "dataset_name",
                           "PublishXRefId")
            selected_traits = tuple(tuple(item[key] for key in filter_keys)
                                    for item in json.loads(selected))
            linked = tuple(tuple(row[key] for key in filter_keys)
                           for row in linked_phenotype_data(
                                   authconn, gn3conn, species))
            page = 1
            count = 0
            while count < per_page:
                results = tuple(remove_linked(
                    remove_selected(
                        do_search(host, search_query, per_page, page),
                        selected_traits),
                    linked))[0:per_page-count]
                count = count + len(results)
                page = page + 1
                save_to_redis(redisconn, redisname, results)
        except NoSearchResults as _nsr:
            pass
        except Exception as _exc: # pylint: disable=[broad-except]
            redisconn.hset(redisname, "status", "failed")
            redisconn.hset(redisname, "exception", traceback.format_exc())
            expire_redis_results(redisconn, redisname)
            return 1
        redisconn.hset(redisname, "status", "completed")
        expire_redis_results(redisconn, redisname)
        return 0

if __name__ == "__main__":
    search() # pylint: disable=[no-value-for-parameter]
