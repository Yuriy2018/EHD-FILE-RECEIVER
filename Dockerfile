FROM python:3.12
COPY . .
RUN pip install --no-cache-dir -r requirements.txt && pip install uvicorn
CMD ["uvicorn", "main:app", "--workers", "2", "--port", "8080", "--host", "0.0.0.0"]
