import requests
import sys
import time
import string
import json
import os
from client import GeneNetworkQAClient
from response import DocIDs, the_doc_ids


baseUrl           = 'https://genenetwork.fahamuai.com/api/tasks'
answerUrl         = baseUrl + '/answers'
basedir           = os.path.abspath(os.path.dirname(__file__))
apiClient         = GeneNetworkQAClient(requests.Session(), api_key='')






def formatBibliographyInfo(bibInfo):
    if isinstance(bibInfo, str):
        # remove '.txt'
        bibInfo = bibInfo.removesuffix('.txt')
    elif isinstance(bibInfo, dict):
        # format string bibliography information
        bibInfo = "{0}. ".format(bibInfo['author'], bibInfo['title'], bibInfo['year'], bibInfo['doi'])
    return bibInfo


def askTheDocuments( extendUrl, my_auth ):
    try:
        res     = requests.post(baseUrl+extendUrl,
                            data={},
                            headers=my_auth)
        res.raise_for_status()
    except:
        raise # what
    if (res.status_code != 200):
        return negativeStatusMsg(res), 0
    task_id     = getTaskIDFromResult(res)
    res         = getAnswerUsingTaskID(task_id, my_auth)
    if (res.status_code != 200):
        return negativeStatusMsg(res), 0
    return res, 1

def getAnswerUsingTaskID( extendUrl, my_auth ):
    try:
        res = requests.get(answerUrl+extendUrl, data={}, headers=my_auth)
        res.raise_for_status()
    except:
        raise
    return res

def openAPIConfig():
    f = open(os.path.join(basedir, "api.config.json") , "rb" )
    result = json.load(f)
    f.close()
    return result


def getTaskIDFromResult(res):
    task_id = json.loads(res.text)
    result  = '?task_id=' + str(task_id['task_id'])
    return result

def negativeStatusMsg(res):
    return 'Problems\n\tStatus code => {0}\n\tReason=> {res.reason}'.format(res.status_code, res.reason)

def filterResponseText(val):
    return json.loads(''.join([str(char) for char in val if char in string.printable]))

def getGNQA(query):
    res, task_id = apiClient.ask('?ask=' + query)
    res, success = apiClient.get_answer(task_id)

    if ( success == 1 ):
        respText       = filterResponseText(res.text)
        if respText.get("data") is None:
            return  "Unfortunately I have nothing on the query",[]
        answer         = respText['data']['answer']
        context        = respText['data']['context']
        references = parse_context(context)
        return answer,references
    else:
        return res, "Unfortunately I have nothing."



def parse_context(context):
    """parse content map id to reference"""
    result = []
    for doc_ids,summary in context.items():
        comboTxt = ""
        for entry  in summary:
            comboTxt += '\t' + entry['text']

        docInfo = the_doc_ids.getInfo(doc_ids)
        if doc_ids !=docInfo:
            bibInfo = formatBibliographyInfo(docInfo)

        else:
            bibInfo = doc_ids
        result.append({"doc_id":doc_ids,"bibInfo":bibInfo,"comboTxt":comboTxt})
    return result