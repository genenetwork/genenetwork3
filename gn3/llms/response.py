
# pylint: skip-file
import string
import json
import os


basedir           = os.path.abspath(os.path.dirname(__file__))


class DocIDs():
    def __init__(self):
        # open doc ids for GN refs
        self.doc_ids = self.loadFile("doc_ids.json")
        # open doc ids for Diabetes references
        self.sugar_doc_ids = self.loadFile("sugar_doc_ids.json")
        # format is not what I prefer, it needs to be rebuilt
        self.formatDocIDs(self.sugar_doc_ids)

    def loadFile(self, file_name):
        file_path = os.path.join(basedir, file_name)
        if os.path.isfile(file_path):
            f = open(file_path, "rb")
            result = json.load(f)
            f.close()
            return result
        else:
            raise Exception("\n{0} -- File does not exist\n".format(file_path))
    
    def formatDocIDs(self, values):
        for _key, _val in values.items():
            if isinstance(_val, list):
                for theObject in _val:
                    docName = self.formatDocumentName(theObject['filename'])
                    docID   = theObject['id']
                    self.doc_ids.update({docID: docName})
                    
    def formatDocumentName(self, val):
       result = val.removesuffix('.pdf') 
       result = result.removesuffix('.txt') 
       result = result.replace('_', ' ')
       return result


    def getInfo(self, doc_id):
        if doc_id in self.doc_ids.keys():
            return self.doc_ids[doc_id]
        else:
            return doc_id

class RespContext():
    def __init__(self, context):
        self.cntxt = context
        self.theObj = {}

    def parseIntoObject(self, info):
        # check for obj, arr, or val
        for key, val in info.items():
            if isinstance(val, list):
                self.parseIntoObject(val)
            elif isinstance(val, str) or isinstance(val, int):
                self.theObj[key] = val
            self.theObj[key] = self.val


def createAccordionFromJson(theContext):
    result = ''
    # loop thru json array
    ndx = 0
    for docID, summaryLst in theContext.items():
        # item is a key with a list
        comboTxt = ''
        for entry in summaryLst:
            comboTxt += '\t' + entry['text']
    return result