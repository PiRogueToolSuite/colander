import logging

import requests
from django.conf import settings

from colander.core.models import BackendCredentials

logger = logging.getLogger(__name__)


class ThreatrClient:
    backend_identifier = 'threatr'
    url = settings.THREATR_BASE_URL

    def __init__(self):
        self.api_key = ''
        self.types = []
        self.supported_types = {}
        self.__load_credentials()
        self.__correctly_configured, self.__error_message = self.is_correctly_configured()

    def is_correctly_configured(self):
        if not self.api_key:
            return False, 'No Threatr API key found, check the documentation.'
        try:
            response = requests.head(f'{self.url}/api/schema/', headers=self.__get_headers(), timeout=10)
            return response.status_code == 200, ''
        except requests.exceptions.RequestException as e:
            logger.error(e)
            return False, 'Unable to retrieve the API schema (https://<threatr domain>/api/schema/)'

    def is_online(self):
        if not self.__correctly_configured:
            return False
        try:
            requests.head(f'{self.url}/api/schema/', headers=self.__get_headers(), timeout=10)
            return True
        except requests.exceptions.RequestException:
            return False

    def __get_headers(self):
        """
        Construct the authentication headers.
        :return: the authentication headers
        """
        return {'Authorization': f'Token {self.api_key}'}

    def __load_credentials(self):
        """
        Load the authentication credentials from the database.
        """
        credentials = BackendCredentials.objects.filter(backend=ThreatrClient.backend_identifier)
        if credentials:
            credentials = credentials.first()
            self.api_key = credentials.credentials.get('api_key', '')

    def get_types(self):
        """
        Get all the types defined in Threatr models.
        :return: all the types defined in Threatr models
        """
        if not self.__correctly_configured:
            self.types = []
            return self.types
        if self.types:
            return self.types
        response = requests.get(f'{self.url}/api/types/', headers=self.__get_headers())
        if response.status_code < 300:
            self.types = response.json()
        return self.types

    def get_supported_types(self):
        """
        Get all the entity types supported by the modules available on Threatr.
        The data returned has the following structure:
        {
          "models": [
            {"name": "Observable"}
          ],
          "types": {
            "Observable": [
              {"id": "CVE", "label": "CVE", "name": "CVE"},
              {"id": "DNS_RECORD", "label": "DNS record", "name": "DNS record"},
              {"id": "DOMAIN", "label": "Domain", "name": "Domain"}
            ]
          }
        }

        This structure is directly compatible with the dynamic type selector used by both
        the investigate workspace and the quick entity creation form.

        :return: the entity types supported by the modules available on Threatr
        """
        if not self.__correctly_configured:
            self.supported_types = {}
            return self.supported_types
        if self.supported_types:
            return self.supported_types
        response = requests.get(f'{self.url}/api/types/supported/', headers=self.__get_headers())
        if response.status_code < 300:
            self.supported_types = response.json()
        return self.supported_types

    def send_request(self, data) -> (list, bool):
        """
        Send the request to Threatr. If Threatr returns a status code equals to 201,
        this means the client has to come back later.

        If the status code is equal to 200, we are ready to return the result to the client.

        The data sent to Threatr must follow this structure:
        {
            "super_type": # the entity super type such as observable or device,
            "type": # the entity type such as IPv4 or server,
            "value": # the actual subject of the search such as 1.1.1.1,
            "force": # indicated to Threatr that it must propagate the query to the
                       different vendors and update its cache
        }

        :param data: the data to be sent
        :return: the query results and a boolean telling if the client has to wait and come back later
        """
        if not self.__correctly_configured:
            return [], False
        if not data:
            return [], False
        response = requests.post(f'{self.url}/api/request/', headers=self.__get_headers(), json=data)
        if response.status_code == 201:
            return [], True
        elif response.status_code == 200:
            return response.json(), False
        else:
            return [], False
