from datetime import datetime
from logging import Logger

import uuid
import requests
import xmltodict

from helpers import XmlSigner


class SmartBridge:

    def __init__(self, test_url: str, production_url: str, xml_signer: XmlSigner, logger: Logger):
        self.__test_url: str = test_url
        self.__production_url: str = production_url
        self.__xml_signer: XmlSigner = xml_signer
        self.__logger: Logger = logger

    async def send_request(self, xml: str, service_id: str, test: bool = False, replace: bool = True,
                           return_object: bool = True) -> dict | None:
        """
            Method that signs XML request and sends it to the source

            Args:
                xml (str): XML that should be signed with ShepXmlSigner
                service_id (str): serviceId of request from SB
                test (bool): Is request will be sent to test environment or not
                replace (bool): Is \\n and \\r should be replaced before signing or not
                return_object (bool): If method should return dict or plain XML text

            Returns:
                xml (str): Response from source in XML format
        """

        address = self.__test_url if test else self.__production_url
        xml = (xml.replace('{serviceId}', service_id)
               .replace('{messageId}', str(uuid.uuid4()))
               .replace('{sessionId}', str(uuid.uuid4()))
               .replace('{messageDate}', datetime.now().strftime("%Y-%m-%dT%H:%M:%S")))
        xml = await self.__xml_signer.sign_shep_request(xml=xml, test=test, replace=replace)

        # noinspection HttpUrlsUsage
        url = f"http://{address}/bip-sync-wss-gost/"

        headers = {
            "Content-Type": "application/xml; charset=utf-8"
        }

        response = requests.post(url=url, data=xml.encode('utf-8'), headers=headers)

        if response.status_code != 200:
            response_text = response.text
            if response_text and isinstance(response_text, str):
                response_text = response_text.replace('&lt;', '<').replace('&gt;', '>')

            self.__logger.error(f'Request to SHEP with {address} failed with response body {response_text}')
            response.raise_for_status()

        response.encoding = "utf-8"
        data = response.text
        if not return_object:
            return data if data else None

        if not data:
            return {}

        parsed = xmltodict.parse(data)
        response_dict = self.__find_node(parsed, 'Envelope', 'Body', 'SendMessageResponse', 'response')

        return {
            'response_info': response_dict.get('responseInfo'),
            'response_data': response_dict.get('responseData'),
        }

    @staticmethod
    def __find_node(node: dict, *path: str) -> dict:
        """Спуск по дереву без учёта namespace-префиксов (ns1:/ns2:/soap:)."""
        current = node
        for name in path:
            for key, value in current.items():
                if key == name or key.endswith(f':{name}'):
                    current = value
                    break
            else:
                raise KeyError(f'{name} not found in response')
        return current
