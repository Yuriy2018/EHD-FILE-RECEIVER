import requests

from logging import Logger


class XmlSigner:
    HEADERS = {
        "Content-Type": "application/json",
    }

    def __init__(self, url: str, logger: Logger):
        self.__url: str = url
        self.__logger: Logger = logger

    async def send_sign_request(self, sign_type: str, payload: dict) -> str | None:
        """
            Method that sends sign request to ShepXmlSigner service

            Args:
                sign_type (str): Route type used for sending request ('xml', 'shep')
                payload (object): Payload data

            Returns:
                xml (object): signed XML
        """

        response = requests.post(url=f"{self.__url}/sign/{sign_type}", json=payload, headers=self.HEADERS)
        if response.status_code != 200:
            self.__logger.error(f'Request for XML sign service failed with response body {response.text}')
            response.raise_for_status()

        data = response.json()

        if data and data.get('xml'):
            data = str(data.get('xml')).replace('<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>', '')
            return data

        return None

    async def sign_xml(self, xml: str) -> str | None:
        """
            Method that signs XML using ShepXmlSigner service

            Args:
                xml (str): XML that should be signed with ShepXmlSigner

            Returns:
                xml (str): signed XML
        """

        payload = {
            "xml": xml
        }

        return await self.send_sign_request(sign_type='xml', payload=payload)

    async def sign_shep_request(self, xml: str, test: bool, replace: bool) -> str | None:
        """
            Method that signs final XML request using ShepXmlSigner service

            Args:
                xml (str): XML that should be signed with ShepXmlSigner
                test (bool): Is request will be sent to test environment or not
                replace (bool): Is \\n and \\r should be replaced before signing or not

            Returns:
                xml (str): signed XML
        """

        payload = {
            "xml": xml,
            "test": test,
            "replace": replace
        }

        return await self.send_sign_request(sign_type='shep', payload=payload)
