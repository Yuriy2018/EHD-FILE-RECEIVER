class EmptyResponse(Exception):
    """Пустой или неожиданный ответ от сервиса."""


class ShepServiceError(Exception):
    """Сервис вернул ошибку в теле ответа."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f'{code}: {message}')


class FileGatewayRejection(Exception):
    """Шлюз принял и обработал сообщение (success=false с бизнес-описанием причины)."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
