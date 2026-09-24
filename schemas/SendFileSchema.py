from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# По XSD FileData.ext — xs:enumeration
FileExt = Literal['jpg', 'png', 'jpeg', 'pdf', 'doc', 'docx']

# По документации operationType: create/update/delete. В XSD просто xs:string,
# но семантика фиксирована — валидируем на входе.
OperationType = Literal['CREATE', 'UPDATE', 'DELETE']


class FileData(BaseModel):
    content: str = Field(..., min_length=1, description="Содержимое файла в base64")
    file_name: str = Field(..., min_length=1, description="Имя файла с расширением")
    ext: FileExt = Field(..., description="Расширение файла (jpg/png/jpeg/pdf/doc/docx)")


class SendFileRequest(BaseModel):
    event_id: str = Field(..., description="Уникальный UUID события")
    file_id: str = Field(..., description="Идентификатор файла")
    operation_type: OperationType = Field(..., description="Тип операции")
    mis_id: int = Field(..., description="Идентификатор МИС")
    send_date: datetime = Field(..., description="Дата и время запроса (ISO 8601, желательно с таймзоной)")
    file: FileData = Field(..., description="Данные файла и base64-контент")
    signed_data: str | None = Field(default=None, description="Подписанные данные в формате JSON (опционально)")
    signature: str | None = Field(default=None, description="Бизнес-подпись данных (опционально)")
