# pylint: skip-file
import json
import string
import os
import datetime
import time
import requests

from requests import Session
from urllib.parse import urljoin
from requests.packages.urllib3.util.retry import Retry
from requests import HTTPError
from requests import Session
from requests.adapters import HTTPAdapter
from urllib.request import urlretrieve
from urllib.parse import quote

basedir = os.path.join(os.path.dirname(__file__))


class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, timeout, *args, **kwargs):
        """TimeoutHTTPAdapter constructor.
        Args:
            timeout (int): How many seconds to wait for the server to send data before
                giving up.
        """
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        """Override :obj:`HTTPAdapter` send method to add a default timeout."""
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout

        return super().send(request, **kwargs)


class GeneNetworkQAClient(Session):
    """GeneNetworkQA Client

    This class provides a client object interface to the GeneNetworkQA API.
    It extends the `requests.Session` class and includes authorization, base URL,
    request timeouts, and request retries.

    Args:
        account (str): Base address subdomain.
        api_key (str): API key.
        version (str, optional): API version, defaults to "v3".
        timeout (int, optional): Timeout value, defaults to 5.
        total_retries (int, optional): Total retries value, defaults to 5.
        backoff_factor (int, optional): Retry backoff factor value, defaults to 30.

    Usage:
        from genenetworkqa import GeneNetworkQAClient
        gnqa = GeneNetworkQAClient(account="account-name", api_key="XXXXXXXXXXXXXXXXXXX...")
    """

    BASE_URL = 'https://genenetwork.fahamuai.com/api/tasks'

    def __init__(self, account, api_key, version="v3", timeout=5, total_retries=5, backoff_factor=30):
        super().__init__()
        self.headers.update(
            {"Authorization": "Bearer " + api_key})
        self.answer_url = f"{self.BASE_URL}/answers"
        self.feedback_url = f"{self.BASE_URL}/feedback"

        adapter = TimeoutHTTPAdapter(
            timeout=timeout,
            max_retries=Retry(
                total=total_retries,
                status_forcelist=[429, 500, 502, 503, 504],
                backoff_factor=backoff_factor,
            ),
        )

        self.mount("https://", adapter)
        self.mount("http://", adapter)

    @staticmethod
    def format_bibliography_info(bib_info):

        if isinstance(bib_info, str):
            # Remove '.txt'
            bib_info = bib_info.removesuffix('.txt')
        elif isinstance(bib_info, dict):
            # Format string bibliography information
            bib_info = "{0}.{1}.{2}.{3} ".format(bib_info.get('author', ''),
                                                 bib_info.get('title', ''),
                                                 bib_info.get('year', ''),
                                                 bib_info.get('doi', ''))
        return bib_info

    @staticmethod
    def ask_the_documents(extend_url, my_auth):
        try:
            response = requests.post(
                base_url + extend_url, data={}, headers=my_auth)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # Handle the exception appropriately, e.g., log the error
            raise RuntimeError(f"Error making the request: {e}")

        if response.status_code != 200:
            return negative_status_msg(response), 0

        task_id = get_task_id_from_result(response)
        response = get_answer_using_task_id(task_id, my_auth)

        if response.status_code != 200:

            return negative_status_msg(response), 0

        return response, 1

    @staticmethod
    def negative_status_msg(response):
        return f"Problems\n\tStatus code => {response.status_code}\n\tReason => {response.reason}"

    def ask(self, exUrl, *args, **kwargs):
        askUrl = self.BASE_URL + exUrl
        res = self.custom_request('POST', askUrl, *args, **kwargs)
        if (res.status_code != 200):
            return self.negativeStatusMsg(res), 0
        task_id = self.getTaskIDFromResult(res)
        return res, task_id

    def get_answer(self, taskid, *args, **kwargs):
        query = self.answer_url + self.extendTaskID(taskid)
        res = self.custom_request('GET', query, *args, **kwargs)
        if (res.status_code != 200):
            return self.negativeStatusMsg(res), 0
        return res, 1

    def custom_request(self, method, url, *args, **kwargs):

        max_retries = 20
        retry_delay = 10

        response = super().request(method, url, *args, **kwargs)

        for i in range(max_retries):
            try:

                response.raise_for_status()
            except requests.exceptions.RequestException as exc:
                code = exc.response.status_code
                if code == 422:
                    raise UnprocessableEntity(exc.request, exc.response)
                    # from exc
                elif i == max_retries - 1:
                    raise exc
            if response.ok:
                # Give time to get all the data
                time.sleep(retry_delay*2)
                return response
            else:
                time.sleep(retry_delay)
        return response

    @staticmethod
    def get_task_id_from_result(response):
        task_id = json.loads(response.text)
        result = f"?task_id={task_id.get('task_id', '')}"
        return result

    @staticmethod
    def get_answer_using_task_id(extend_url, my_auth):
        try:
            response = requests.get(
                answer_url + extend_url, data={}, headers=my_auth)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as error:
            # Handle the exception appropriately, e.g., log the error
            raise error

    @staticmethod
    def filter_response_text(val):
        """
        Filters out non-printable characters from the input string and parses it as JSON.

        Args:
            val (str): Input string to be filtered and parsed.

        Returns:
            dict: Parsed JSON object.
        # remove  this
        """
        return json.loads(''.join([str(char) for char in val if char in string.printable]))

    def getTaskIDFromResult(self, res):
        return json.loads(res.text)

    def extendTaskID(self, task_id):
        return '?task_id=' + str(task_id['task_id'])

    def get_gnqa(self, query):
        qstr = quote(query)
        res, task_id = api_client.ask('?ask=' + qstr)
        res, success = api_client.get_answer(task_id)

        if success == 1:
            resp_text = filter_response_text(res.text)
            answer = resp_text.get('data', {}).get('answer', '')
            context = resp_text.get('data', {}).get('context', '')
            return answer, context
        else:
            return res, "Unfortunately, I have nothing."

