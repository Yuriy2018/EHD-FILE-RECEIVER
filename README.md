# MZRK-S-8579 — EHD-FILE-RECEIVER

Сервис передачи файлов в EHD (`http://mz.kz/exd/integration`, `RequestMessage`/`ResponseMessage`).
`serviceId = EHD-FILE-RECEIVER`, `epir_id = MZRK-S-8579`.

## Endpoint

### `POST /files`

Один метод интеграции: передача содержимого файла в base64 + метаданные + опционально
подписанные данные и цифровая подпись.

Полный запрос:
```json
{
  "event_id": "123e4567-e89b-12d3-a456-426614174000",
  "file_id": "file-9876543210",
  "operation_type": "CREATE",
  "mis_id": 42,
  "send_date": "2025-05-15T10:30:00+05:00",
  "file": {
    "content": "SGVsbG8gd29ybGQhIENvbnRlbnQgb2YgZG9jdW1lbnQucGRm",
    "file_name": "document.pdf",
    "ext": "pdf"
  },
  "signed_data": "{\"eventId\":\"...\",\"fileId\":\"file-9876543210\"}",
  "signature": "MEUCIQDv3JfQW+Yg1zjmZq5N9sHJeU8bQqZTXq4Yq7mZQh2j5AIgP5JzN0xvX2fK7"
}
```

Минимальный (без опциональных полей):
```json
{
  "event_id": "evt-1",
  "file_id": "f-1",
  "operation_type": "DELETE",
  "mis_id": 1,
  "send_date": "2025-01-01T00:00:00",
  "file": {
    "content": "AAAA",
    "file_name": "a.png",
    "ext": "png"
  }
}
```

Успешный ответ (`HTTP 200`):
```json
{
  "success": true,
  "message": "Операция выполнена успешно"
}
```

## Валидация запроса

- `operation_type` — `CREATE` / `UPDATE` / `DELETE` (по документации XSD).
- `file.ext` — `jpg` / `png` / `jpeg` / `pdf` / `doc` / `docx` (по `xs:enumeration`).
- `file.content`, `file.file_name` — `minLength 1`.
- `send_date` — ISO 8601 datetime (лучше с таймзоной).

## HTTP-коды ошибок

- `422` — шлюз ответил транспортным `SUCCESS`, но `success=false` в теле (бизнес-отказ, напр. невалидная подпись). Тело: `{"success": false, "message": "…"}`.
- `523` — SHEP вернул ошибку в `responseInfo/status`, либо пустой ответ, либо не удалось достучаться.
- `500` — прочие непредвиденные ошибки.

## Особенности

- **Namespace `elementFormDefault` в XSD не указан → `unqualified`**: дочерние элементы `<data>` идут без префикса (в отличие от `EHD-CHECK-STATUS-RECEIVER`, где `elementFormDefault="qualified"` требовал `int:`). Тот же targetNamespace, но разные правила формирования — важно не спутать.
- **Коды успеха на транспортном уровне**: принимаются `200`, `SUCCESS`, `SCSS*`. Всё остальное — `ShepServiceError`.
- **Все текстовые поля запроса экранируются** (`<`, `>`, `&`) через `xml.sax.saxutils.escape` перед вставкой в шаблон.
- **`sendDate` форматируется через `datetime.isoformat()`** — для tz-aware дат это даёт `2025-05-15T10:30:00+05:00`.

## Локальный запуск

```bash
pip install -r requirements.txt
python main.py
```

## Docker

```bash
docker build -t mzrk-s-8579 .
docker run --rm -p 6063:8080 mzrk-s-8579
```
