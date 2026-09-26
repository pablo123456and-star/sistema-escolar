# Imagen para desplegar la API (Railway u otro servidor con Docker)
FROM python:3.14-slim

WORKDIR /app

COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock

COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
