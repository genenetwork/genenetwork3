"""this module contains code for processing response from fahamu client.py"""
# pylint: disable=C0301
import os
import string
import json
import logging
import requests

from urllib.parse import urljoin
from urllib.parse import quote

from gn3.llms.client import GeneNetworkQAClient


BASE_URL = 'https://genenetwork.fahamuai.com/api/tasks'
BASEDIR = os.path.abspath(os.path.dirname(__file__))


class DocIDs():
    """ Class Method to Parse document id and names from files"""
    def __init__(self):
        """
        init method for Docids
        * doc_ids.json: opens doc)ids for gn references
        * sugar_doc_ids:  open doci_ids for diabetes references
        """
        self.doc_ids = self.load_file("doc_ids.json")
        self.sugar_doc_ids = self.load_file("all_files.json")
        self.format_doc_ids(self.sugar_doc_ids)

    def load_file(self, file_name):
        """Method to load and read doc_id files"""
        file_path = os.path.join(BASEDIR, file_name)
        if os.path.isfile(file_path):
            with open(file_path, "rb") as file_handler:
                return json.load(file_handler)
        else:
            raise FileNotFoundError(f"{file_path}-- FIle does not exist\n")

    def format_doc_ids(self, docs):
        """method to format doc_ids for list items"""
        for _key, val in docs.items():
            if isinstance(val, list):
                for doc_obj in val:
                    doc_name = doc_obj["filename"].removesuffix(".pdf").removesuffix(".txt").replace("_", "")
                    self.doc_ids.update({doc_obj["id"]:  doc_name})

    def get_info(self, doc_id):
        """ interface to make read from doc_ids"""
        if doc_id in self.doc_ids.keys():
            return self.doc_ids[doc_id]
        else:
            return doc_id


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


def load_file(filename, dir_path):
    """function to open and load json file"""
    file_path = os.path.join(dir_path, f"{filename}")
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"{filename} was not found or is a directory")
    with open(file_path, "rb") as file_handler:
        return json.load(file_handler)


def fetch_pubmed(references, file_name, data_dir=""):
    """method to fetch and populate references with pubmed"""

    try:
        pubmed = load_file(file_name, os.path.join(data_dir, "gn-meta/lit"))
        for reference in references:
            if pubmed.get(reference["doc_id"]):
                reference["pubmed"] = pubmed.get(reference["doc_id"])
        return references

    except FileNotFoundError:
        logging.error("failed to find pubmed_path for %s/%s",
                      data_dir, file_name)
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
            return task_id, "Please try to rephrase your question to receive feedback", []
        answer = resp_text['data']['answer']
        context = resp_text['data']['context']
        references = parse_context(
            context, DocIDs().get_info, format_bibliography_info)
        references = fetch_pubmed(references, "pubmed.json", tmp_dir)

        return task_id, answer, references
    else:
        return task_id, "Please try to rephrase your question to receive feedback", []


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
    return [query for query in
            [result.partition("-")[2] for result in results] if query != ""]
