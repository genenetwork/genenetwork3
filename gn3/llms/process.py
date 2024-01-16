
# pylint: skip-file

import requests
import sys
import time
import string
import json
import os
from urllib.request import urlretrieve
from urllib.parse import quote

from urllib.parse import urljoin

from gn3.llms.client import GeneNetworkQAClient
from gn3.llms.response import DocIDs


baseUrl = 'https://genenetwork.fahamuai.com/api/tasks'
answerUrl = baseUrl + '/answers'
basedir = os.path.abspath(os.path.dirname(__file__))


def formatBibliographyInfo(bibInfo):
    if isinstance(bibInfo, str):
        # remove '.txt'
        bibInfo = bibInfo.removesuffix('.txt')
    elif isinstance(bibInfo, dict):
        # format string bibliography information
        bibInfo = "{0}.{1}.{2}.{3} ".format(
            bibInfo['author'], bibInfo['title'], bibInfo['year'], bibInfo['doi'])
    return bibInfo


def askTheDocuments(extendUrl, my_auth):
    try:
        res = requests.post(baseUrl+extendUrl,
                            data={},
                            headers=my_auth)
        res.raise_for_status()
    except:
        raise  # what
    if (res.status_code != 200):
        return negativeStatusMsg(res), 0
    task_id = getTaskIDFromResult(res)
    res = getAnswerUsingTaskID(task_id, my_auth)
    if (res.status_code != 200):
        return negativeStatusMsg(res), 0
    return res, 1


def getAnswerUsingTaskID(extendUrl, my_auth):
    try:
        res = requests.get(answerUrl+extendUrl, data={}, headers=my_auth)
        res.raise_for_status()
    except:
        raise
    return res


def openAPIConfig():
    f = open(os.path.join(basedir, "api.config.json"), "rb")
    result = json.load(f)
    f.close()
    return result


def getTaskIDFromResult(res):
    task_id = json.loads(res.text)
    result = '?task_id=' + str(task_id['task_id'])
    return result


def negativeStatusMsg(res):
    # mypy: ignore
    return 'Problems\n\tStatus code => {0}\n\tReason=> {1}'.format(res.status_code, res.reason)


def filterResponseText(val):
    return json.loads(''.join([str(char) for char in val if char in string.printable]))


def getGNQA(query, auth_token):
    apiClient = GeneNetworkQAClient(requests.Session(), api_key=auth_token)
    res, task_id = apiClient.ask('?ask=' + quote(query), auth_token)
    res, success = apiClient.get_answer(task_id)

    if (success == 1):
        respText = filterResponseText(res.text)
        if respText.get("data") is None:
            return "Unfortunately I have nothing on the query", []
        answer = respText['data']['answer']
        context = respText['data']['context']
        references = parse_context(context)
        return task_id, answer, references
    else:
        return task_id, res, "Unfortunately I have nothing."


def parse_context(context):
    """parse content map id to reference"""
    result = []
    for doc_ids, summary in context.items():
        comboTxt = ""
        for entry in summary:
            comboTxt += '\t' + entry['text']

        docInfo = DocIDs().getInfo(doc_ids)
        if doc_ids != docInfo:
            bibInfo = formatBibliographyInfo(docInfo)

        else:
            bibInfo = doc_ids
        result.append(
            {"doc_id": doc_ids, "bibInfo": bibInfo, "comboTxt": comboTxt})
    return result


def rate_document(task_id, doc_id, rating, auth_token):
    """This method is used to provide feedback for a document by making a rating."""
    try:
        resp = requests.post(
            urljoin(baseUrl, f"/feedback?task_id={task_id}&document_id={doc_id}&feedback={rating}"),
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        resp.raise_for_status()
        return {"status": "success", **resp.json()}
    except requests.exceptions.HTTPError as http_error:
        raise RuntimeError(f"HTTP Error Occurred: {http_error.response.text} -with status code- {http_error.response.status_code}")
    except Exception as error:

        raise RuntimeError(f"An error occurred: {str(error)}")
