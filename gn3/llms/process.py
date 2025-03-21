"""this module contains code for processing response from fahamu client.py"""
# pylint: disable=C0301
import os
import re
import string
import json
import logging
from urllib.parse import quote

from gn3.llms.client import GeneNetworkQAClient


BASE_URL = 'https://balg-qa.genenetwork.org/api/tasks'
BASEDIR = os.path.abspath(os.path.dirname(__file__))


class DocIDs():
    """ Class Method to Parse document id and names from files"""
    def __init__(self):
        """
        init method for Docids
        * doc_ids.json: open doc_ids for gn references
        * sugar_doc_ids:  open doc_ids for diabetes references
        """
        self.doc_ids = load_file("doc_ids.json", BASEDIR)
        sugar_doc_ids = load_file("all_files.json", BASEDIR)
        self.format_doc_ids(sugar_doc_ids)

    def format_doc_ids(self, docs):
        """method to format doc_ids for list items doc_id and doc_name"""
        for _key, val in docs.items():
            if isinstance(val, list):
                for doc_obj in val:
                    doc_name = doc_obj["filename"].removesuffix(".pdf").removesuffix(".txt").replace("_", "")
                    self.doc_ids.update({doc_obj["id"]:  doc_name})

    def get_info(self, doc_id):
        """ interface to make read from doc_ids
           and extract info data  else returns
           doc_id
        Args:
            doc_id: str: a search key for doc_ids
        Returns:
              an object if doc id exists else
              raises a KeyError
        """
        return self.doc_ids[doc_id]

def format_bibliography_info(bib_info):
    """Utility function for formatting bibliography info
    """
    if isinstance(bib_info, str):
        return bib_info.removesuffix('.txt')
    elif isinstance(bib_info, dict):
        return f"{bib_info['author']}.{bib_info['title']}.{bib_info['year']}.{bib_info['doi']} "
    return bib_info


def parse_context(context, get_info_func, format_bib_func):
    """Function to parse doc_ids content
     Args:
         context: raw references from  fahamu api
         get_info_func: function to get doc_ids info
         format_bib_func:  function to foramt bibliography info
    Returns:
          an list with each item having (doc_id,bib_info,
          combined reference text)
    """
    results = []
    for doc_ids, summary in context.items():
        combo_txt = ""
        for entry in summary:
            combo_txt += "\t" + entry["text"]
        try:
            doc_info = get_info_func(doc_ids)
            bib_info = format_bib_func(doc_info)
        except KeyError:
            bib_info = doc_ids
        pattern = r'(https?://|www\.)[\w.-]+(\.[a-zA-Z]{2,})([/\w.-]*)*'
        combo_text = re.sub(pattern,
                            lambda x: f"<a href='{x[0]}' target=_blank> {x[0]} </a>",
                            combo_txt)
        results.append(
            {"doc_id": doc_ids, "bibInfo": bib_info,
             "comboTxt": combo_text})
    return results


def load_file(filename, dir_path):
    """Utility function to read json file
    Args:
        filename:  file name to read
        dir_path:  base directory for the file
    Returns: json data read to a dict
    """
    with open(os.path.join(dir_path, f"{filename}"),
              "rb") as file_handler:
        return json.load(file_handler)


def fetch_pubmed(references, file_name, data_dir=""):
    """
    Fetches PubMed data from a JSON file and populates the\
    references dictionary.

    Args:
        references (dict): Dictionary with document IDs as keys\
    and reference data as values.
        filename (str): Name of the JSON file containing PubMed data.
        data_dir (str): Base directory where the data files are located.

    Returns:
        dict: Updated references dictionary populated with the PubMed data.
    """
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


def get_gnqa(query, auth_token, data_dir=""):
    """entry function for the gn3 api endpoint()
    ARGS:
         query: what is  a gene
         auth_token: token to connect to api_client
         data_dir:  base datirectory for gn3 data
    Returns:
         task_id: fahamu unique identifier for task
         answer
         references: contains doc_name,reference,pub_med_info
    """
    api_client = GeneNetworkQAClient(api_key=auth_token)
    res, task_id = api_client.ask('?ask=' + quote(query), query=query)
    res, _status = api_client.get_answer(task_id)
    resp_text = json.loads(''.join([str(char)
                           for char in res.text if char in string.printable]))
    answer = re.sub(r'(https?://|www\.)[\w.-]+(\.[a-zA-Z]{2,})([/\w.-]*)*',
                    lambda x: f"<a href='{x[0]}' target=_blank> {x[0]} </a>",
                    resp_text["data"]["answer"])
    context = resp_text['data']['context']
    return task_id, answer, fetch_pubmed(parse_context(
                            context, DocIDs().get_info,
                            format_bibliography_info),
                            "pubmed.json", data_dir)
