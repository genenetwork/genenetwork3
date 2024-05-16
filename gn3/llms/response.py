""" Module contains code for parsing references doc_ids """
# pylint: disable=C0301
import json
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class DocIDs():
    """ Class Method to Parse document id and names"""
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
        file_path = os.path.join(basedir, file_name)
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
