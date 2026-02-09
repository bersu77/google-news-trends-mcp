FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir --upgrade pip --default-timeout=500 --retries 10 \
    --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org \
    && pip install --no-cache-dir . --default-timeout=500 --retries 10 \
    --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org

ENV PORT=8080

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
