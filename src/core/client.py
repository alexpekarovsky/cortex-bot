import json
import logging

import requests

from core.config import config

logger = logging.getLogger(__name__)

class PAPIClient:
    def __init__(self, url: str, api_key: str, api_key_id: str):
        self.url = url
        self.api_key = api_key
        self.api_key_id = api_key_id

    def send_request(self, method: str, path: str, data: dict = None, headers: dict = None):
        if not headers:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': self.api_key,
                'X-XDR-AUTH-ID': self.api_key_id
            }
        logger.info(f'Sending request to {self.url}/{path}')
        try:
            response = requests.request(method=method, url=f'{self.url}{path}', data=json.dumps(data), headers=headers)
        except Exception as e:
            logger.exception(f'Failed sending request to server for request to {path}: {e}')
            raise e

        if response is None:
            err_msg = f'Error response from server for request to {path}'
            logger.error(err_msg)
            raise Exception(err_msg)

        if response.status_code < 200 or response.status_code >= 300:
            err_msg = f'Error response from server for request to {path}: {response.content} [{response.status_code}]'
            logger.error(err_msg)
            raise Exception(err_msg)

        return response.json()
