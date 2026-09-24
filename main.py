import logging

import uvicorn

from fastapi import FastAPI, HTTPException

from requests.exceptions import HTTPError
from settings import configurations, get_logger
from helpers import SmartBridge, XmlSigner

from schemas.SendFileSchema import SendFileRequest

from parsers.exceptions import ShepServiceError, EmptyResponse, FileGatewayRejection
from parsers import SendFileParser
from services import SendFileService

logger = get_logger()


class SuppressSuccessAccessLogs(logging.Filter):
    """Пропускает только записи access-лога uvicorn, где статус >= 500."""

    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if not args or len(args) < 5:
            return True
        try:
            status_code = int(args[4])
        except (TypeError, ValueError):
            return True
        return status_code >= 500


def create_app() -> FastAPI:
    service_id = "EHD-FILE-RECEIVER"
    epir_id = "MZRK-S-8579"

    # Дети <data> без namespace-префикса (XSD с unqualified elementFormDefault по умолчанию).
    envelope = """
        <soap:Envelope
        xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <soap:Header/>
        <soap:Body wsu:Id="id-{messageId}">
        <SendMessage xmlns="http://bip.bee.kz/SyncChannel/v10/Types" xmlns:tns="http://mz.kz/exd/integration">
        <request xmlns="">
        <requestInfo>
        <messageId>{messageId}</messageId>
        <serviceId>{serviceId}</serviceId>
        <messageDate>{messageDate}</messageDate>
        <sender>
        <senderId>{username}</senderId>
        <password>{password}</password>
        </sender>
        <sessionId>{sessionId}</sessionId>
        </requestInfo>
        <requestData>
        {requestData}
        </requestData>
        </request>
        </SendMessage>
        </soap:Body>
        </soap:Envelope>
    """

    xml_signer = XmlSigner(url=configurations.shep_xml_signer, logger=logger)
    smart_bridge = SmartBridge(
        test_url=configurations.test_url,
        production_url=configurations.production_url,
        xml_signer=xml_signer,
        logger=logger,
    )

    send_file_parser = SendFileParser(
        smart_bridge=smart_bridge, test=configurations.test, logger=logger,
    )

    send_file_service = SendFileService(
        parser=send_file_parser, service_id=service_id, logger=logger,
    )

    fastapi_app = FastAPI(
        title=epir_id,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @fastapi_app.get('/health-check')
    async def health_check():
        return {'status': 'OK!'}

    # Передача файла в EHD (create/update/delete по operationType)
    @fastapi_app.post('/files')
    async def send_file(request: SendFileRequest):
        try:
            return await send_file_service.load_data(
                envelope=envelope, request=request,
            )
        except FileGatewayRejection as exc:
            # Шлюз ответил транспортным success, но success=false в теле.
            # 422 — семантическая ошибка обработки.
            logger.warning(f'[SendFile] Rejected by gateway: {exc.message}')
            raise HTTPException(status_code=422, detail={'success': False, 'message': exc.message})
        except ShepServiceError as exc:
            logger.error(f'[SendFile] Service error: {exc}')
            raise HTTPException(status_code=523, detail=str(exc))
        except EmptyResponse:
            logger.error('[SendFile] Empty response from SHEP')
            raise HTTPException(status_code=523, detail='Empty response from service')
        except HTTPError as exc:
            logger.error('[SendFile] Internal server error from SHEP')
            raise HTTPException(status_code=523, detail=str(exc))
        except Exception as e:
            logger.exception(f'[SendFile] Unknown exception []: {e}')
            raise HTTPException(status_code=500, detail=str(e))

    return fastapi_app


app = create_app()

if __name__ == "__main__":
    logging.getLogger("uvicorn.access").addFilter(SuppressSuccessAccessLogs())
    uvicorn.run(app, host="0.0.0.0", port=int(configurations.port))
