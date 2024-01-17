
"""this module contains code for processing response from fahamu client.py"""

import string
import json

from urllib.parse import urljoin
from urllib.parse import quote
import requests


from gn3.llms.client import GeneNetworkQAClient
from gn3.llms.response import DocIDs

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


def get_gnqa(query, auth_token):
    """entry function for the gn3 api endpoint()"""

    api_client = GeneNetworkQAClient(requests.Session(), api_key=auth_token)
    res, task_id = api_client.ask('?ask=' + quote(query), auth_token)
    res, success = api_client.get_answer(task_id)
    if success == 1:
        resp_text = filter_response_text(res.text)
        if resp_text.get("data") is None:
            return "Unfortunately I have nothing on the query", []
        answer = resp_text['data']['answer']
        context = resp_text['data']['context']
        references = parse_context(
            context, DocIDs().getInfo, format_bibliography_info)
        return task_id, answer, references
    else:
        return task_id, res, "Unfortunately I have nothing."
