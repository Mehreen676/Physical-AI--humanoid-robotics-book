FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend_v3 backend_v3
COPY retrieval retrieval

EXPOSE 8000

CMD ["uvicorn", "backend_v3.main:app", "--host", "0.0.0.0", "--port", "8000"]
