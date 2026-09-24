from logging import Logger

from parsers import SendFileParser
from schemas.SendFileSchema import SendFileRequest


class SendFileService:
    def __init__(self, parser: SendFileParser, service_id: str, logger: Logger):
        self.parser: SendFileParser = parser
        self.service_id: str = service_id
        self.logger: Logger = logger

    async def load_data(self, envelope: str, request: SendFileRequest) -> dict:
        self.logger.info(
            f'[SendFile] Received request eventId={request.event_id} '
            f'fileId={request.file_id} op={request.operation_type} '
            f'misId={request.mis_id} name={request.file.file_name} ext={request.file.ext} '
            f'contentBytes(base64)={len(request.file.content)}'
        )
        reply: dict = await self.parser.parse(
            service_id=self.service_id, envelope=envelope, request=request,
        )
        self.logger.info(f'[SendFile] Request processed eventId={request.event_id} fileId={request.file_id}')
        return reply
