
"""this module contains code for processing response from fahamu client.py"""

import os
import string
import json

from urllib.parse import urljoin
from urllib.parse import quote
import requests

from gn3.llms.client import GeneNetworkQAClient
from gn3.llms.response import DocIDs
from gn3.settings import TMPDIR


BASE_URL = 'https://genenetwork.fahamuai.com/api/tasks'


# pylint: disable=C0301


def format_bibliography_info(bib_info):
    """Function for formatting bibliography info"""
    if isinstance(bib_info, str):
        return bib_info.removesuffix('.txt')
    elif isinstance(bib_info, dict):
        return f"{bib_info['author']}.{bib_info['title']}.{bib_info['year']}.{bib_info['doi']} "
    return bib_info


def filter_response_text(val):
    """helper function for filtering non-printable chars"""
    return json.loads(''.join([str(char)
                               for char in val if char in string.printable]))


def parse_context(context, get_info_func, format_bib_func):
    """function to parse doc_ids content"""
    results = []
    for doc_ids, summary in context.items():
        combo_txt = ""
        for entry in summary:
            combo_txt += "\t" + entry["text"]
        doc_info = get_info_func(doc_ids)
        bib_info = doc_ids if doc_ids == doc_info else format_bib_func(
            doc_info)
        results.append(
            {"doc_id": doc_ids, "bibInfo": bib_info, "comboTxt": combo_txt})
    return results


def rate_document(task_id, doc_id, rating, auth_token):
    """This method is used to provide feedback for a document by making a rating."""
    # todo move this to clients
    try:
        url = urljoin(BASE_URL,
                      f"""/feedback?task_id={task_id}&document_id={doc_id}&feedback={rating}""")
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = requests.post(url, headers=headers)
        resp.raise_for_status()

        return {"status": "success", **resp.json()}
    except requests.exceptions.HTTPError as http_error:
        raise RuntimeError(f"HTTP Error Occurred:\
            {http_error.response.text} -with status code- {http_error.response.status_code}") from http_error
    except Exception as error:
        raise RuntimeError(f"An error occurred: {str(error)}") from error


def load_file(filename, dir_path):
    """function to open and load json file"""
    file_path = os.path.join(dir_path, f"/{filename}")
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"{filename} was not found or is a directory")
    with open(file_path, "rb") as file_handler:
        return json.load(file_handler)


def fetch_pubmed(references, file_name, tmp_dir=""):
    """method to fetch and populate references with pubmed"""

    try:
        pubmed = load_file(file_name)
        for reference in references:
            if pubmed.get(reference["doc_id"]):
                reference["pubmed"] = pubmed.get(reference["doc_id"])
        return references

    except FileNotFoundError:
        return references


def get_gnqa(query, auth_token, tmp_dir=""):
    """entry function for the gn3 api endpoint()"""

    api_client = GeneNetworkQAClient(requests.Session(), api_key=auth_token)
    res, task_id = api_client.ask('?ask=' + quote(query), auth_token)
    if task_id == 0:
        raise RuntimeError(f"Error connecting to Fahamu Api: {str(res)}")
    res, success = api_client.get_answer(task_id)
    if success == 1:
        resp_text = filter_response_text(res.text)
        if resp_text.get("data") is None:
            return task_id, "Unfortunately I have nothing on the query", []
        answer = resp_text['data']['answer']
        context = resp_text['data']['context']
        references = parse_context(
            context, DocIDs().getInfo, format_bibliography_info)
        references = fetch_pubmed(references, "pubmed.json", tmp_dir)

        return task_id, answer, references
    else:
        return task_id, "Unfortunately, I have nothing on the query", []


def fetch_query_results(query, user_id, redis_conn):
    """this method fetches prev user query searches"""
    result = redis_conn.get(f"LLM:{user_id}-{query}")
    if result:
        return json.loads(result)
    return {
        "query": query,
        "answer": "Sorry No answer for you",
        "references": [],
        "task_id": None
    }


def get_user_queries(user_id, redis_conn):
    """methos to fetch all queries for a specific user"""

    results = redis_conn.keys(f"LLM:{user_id}*")
    return [query for query in [result.partition("-")[2] for result in results] if query != ""]
