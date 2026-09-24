from datetime import datetime
from logging import Logger
from xml.sax.saxutils import escape

from settings import configurations
from helpers import SmartBridge
from schemas.SendFileSchema import SendFileRequest
from .exceptions import EmptyResponse, ShepServiceError, FileGatewayRejection


# Коды из responseInfo/status, которые трактуем как «успешно принято на шлюз».
# Дальше внутри тела <success> может быть true/false — это уже бизнес-исход.
_SUCCESS_STATUS_CODES = {'200', 'SUCCESS'}
_SUCCESS_STATUS_PREFIXES = ('SCSS',)


def _is_success_status(code: str) -> bool:
    if not code:
        # Если код вообще отсутствует — не считаем это ошибкой шлюза,
        # положимся на разбор тела.
        return True
    return code in _SUCCESS_STATUS_CODES or code.startswith(_SUCCESS_STATUS_PREFIXES)


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in ('true', '1')


class SendFileParser:
    def __init__(self, smart_bridge: SmartBridge, test: bool, logger: Logger):
        self.smart_bridge: SmartBridge = smart_bridge
        self.test: bool = test
        self.logger: Logger = logger

    @staticmethod
    def _fmt_send_date(dt: datetime) -> str:
        # По XSD xs:dateTime. isoformat даёт корректный формат;
        # если tz-aware — со смещением, если naive — без.
        return dt.isoformat()

    @classmethod
    def get_template(cls, request: SendFileRequest) -> str:
        signed_data_element = (
            f'<signedData>{escape(request.signed_data)}</signedData>'
            if request.signed_data is not None else ''
        )
        signature_element = (
            f'<signature>{escape(request.signature)}</signature>'
            if request.signature is not None else ''
        )
        # По XSD (elementFormDefault не указан → unqualified) дети <data>
        # без namespace-префикса. Пример запроса это подтверждает.
        return (
            '<data xsi:type="tns:RequestMessage">'
            f'<eventId>{escape(request.event_id)}</eventId>'
            f'<login>{configurations.login}</login>'
            f'<password>{configurations.password}</password>'
            f'<fileId>{escape(request.file_id)}</fileId>'
            f'<operationType>{escape(request.operation_type)}</operationType>'
            f'<misId>{request.mis_id}</misId>'
            f'<sendDate>{cls._fmt_send_date(request.send_date)}</sendDate>'
            '<file>'
            # content — base64, из безопасных для XML символов; escape() — на всякий случай (no-op)
            f'<content>{escape(request.file.content)}</content>'
            f'<file_name>{escape(request.file.file_name)}</file_name>'
            f'<ext>{request.file.ext}</ext>'
            '</file>'
            f'{signed_data_element}'
            f'{signature_element}'
            '</data>'
        )

    @staticmethod
    def get_request(template: str, envelope: str) -> str:
        return envelope.replace('{requestData}', template)

    @classmethod
    def map(cls, response: dict | None) -> dict:
        if not response or not isinstance(response, dict):
            raise EmptyResponse()

        response_info = response.get('response_info') or {}
        status = response_info.get('status') or {}
        status_code = str(status.get('code', ''))

        if not _is_success_status(status_code):
            raise ShepServiceError(status_code, status.get('message', ''))

        response_data = response.get('response_data') or {}
        data = response_data.get('data') or {}
        if not isinstance(data, dict):
            raise EmptyResponse()

        # По XSD ResponseMessage: <success> и <message> — оба required, без префикса.
        success = _to_bool(data.get('success'))
        message = data.get('message') or ''

        # Явный отказ шлюза: 200/SUCCESS на транспортном уровне, но бизнес-логика вернула false.
        # Отдаём как отдельную ошибку — вызывающий код решит, как это показать клиенту.
        if not success:
            raise FileGatewayRejection(message)

        return {
            'success': True,
            'message': message,
        }

    async def parse(self, service_id: str, envelope: str, request: SendFileRequest) -> dict:
        template = self.get_template(request=request)
        request_xml = self.get_request(template=template, envelope=envelope)

        response: dict | None = await self.smart_bridge.send_request(
            xml=request_xml, service_id=service_id, test=self.test
        )
        return self.map(response)
