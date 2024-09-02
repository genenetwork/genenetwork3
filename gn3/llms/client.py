"""Module  Contains code for making request to fahamu Api"""
# pylint: disable=C0301
import json
import time

import requests
from requests import Session
from requests.adapters import HTTPAdapter
from requests.adapters import Retry

from gn3.llms.errors import LLMError


class TimeoutHTTPAdapter(HTTPAdapter):
    """Set a default timeout for HTTP calls """
    def __init__(self, timeout, *args, **kwargs):
        """TimeoutHTTPAdapter constructor."""
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, *args, **kwargs):
        """Override :obj:`HTTPAdapter` send method to add a default timeout."""
        kwargs["timeout"] = (
            kwargs["timeout"] if kwargs.get("timeout") else self.timeout
        )
        return super().send(*args, **kwargs)


class GeneNetworkQAClient(Session):
    """GeneNetworkQA Client

    This class provides a client object interface to the GeneNetworkQA API.
    It extends the `requests.Session` class and includes authorization,
    base URL,
    request timeouts, and request retries.

    Args:
        api_key (str): API key.
        timeout (int, optional): Timeout value, defaults to 5.
        total_retries (int, optional): Total retries value, defaults to 5.
        backoff_factor (int, optional): Retry backoff factor value,
    defaults to 30.

    Usage:
        from genenetworkqa import GeneNetworkQAClient
        gnqa = GeneNetworkQAClient(account="account-name",
    api_key="XXXXXXXXXXXXXXXXXXX...")
    """

    def __init__(self, api_key, timeout=30,
                 total_retries=5, backoff_factor=2):
        super().__init__()
        self.headers.update(
            {"Authorization": "Bearer " + api_key})
        self.base_url = "https://genenetwork.fahamuai.com/api/tasks"
        self.answer_url = f"{self.base_url}/answers"
        self.feedback_url = f"{self.base_url}/feedback"
        self.query = ""

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

    def get_answer_using_task_id(self, extend_url, my_auth):
        """call this method with task id to fetch response"""
        try:
            response = requests.get(
               self.answer_url + extend_url, data={}, headers=my_auth)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as error:
            raise error

    @staticmethod
    def negative_status_msg(response):
        """ handler for non 200 response from fahamu api"""
        return f"Error: Status code -{response.status_code}- Reason::{response.reason}"

    def ask(self, ex_url, query,  *args, **kwargs):
        """fahamu ask api interface"""
        self.query = query
        res = self.custom_request('POST', f"{self.base_url}{ex_url}", *args, **kwargs)
        return res, json.loads(res.text)

    def get_answer(self, task_obj, *args, **kwargs):
        """Fahamu get answer interface"""
        query = f"{self.answer_url}?task_id={task_obj['task_id']}"
        res = self.custom_request('GET', query, *args, **kwargs)
        return res, 1

    def custom_request(self, method, url, *args, **kwargs):
        """
        Make a custom request to the Fahamu API to ask and get a response.
        This is a custom method, which is the current default for fetching items,
        as it overrides the adapter provided above.
        This function was created to debug the slow response rate of Fahamu and
        provide custom a response.
        """
        max_retries = 50
        retry_delay = 3
        response_msg = {
            404: "Api endpoint Does not exist",
            500: "Use of Invalid Token/or the Fahamu Api is currently  down",
            400: "You sent a bad Fahamu request",
            401: "You do not have authorization to perform the request",
        }
        for _i in range(max_retries):
            response = super().request(method, url, *args, **kwargs)
            if response.ok:
                if method.lower() == "get" and not response.json().get("data"):
                    # note this is a dirty trick to check if fahamu has returned the results
                    # the issue is that the api only returns 500 or 200 satus code
                    # TODO: fix this on their end
                    time.sleep(retry_delay)
                    continue
                return response
            else:
                raise LLMError(f"Request error with code:\
                {response.status_code} occurred with reason:\
                {response_msg.get(response.status_code,response.reason)}",
                               self.query)
                #time.sleep(retry_delay)
        raise LLMError("Timeout error: We couldn't provide a response,Please try\
        to rephrase your question to receive feedback",
                       self.query)
