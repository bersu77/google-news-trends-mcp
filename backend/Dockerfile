# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Upgrade pip first
RUN pip install --upgrade pip --default-timeout=100 --retries 5 \
    --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org

# Install core dependencies one by one to leverage layer caching
RUN pip install --no-cache-dir "fastapi>=0.110.0" --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org
RUN pip install --no-cache-dir "uvicorn[standard]==0.24.0" --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org
RUN pip install --no-cache-dir "pydantic[email]==2.5.0" --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org
RUN pip install --no-cache-dir "supabase>=2.3.0" --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org
RUN pip install --no-cache-dir "httpx>=0.27.0" --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org
RUN pip install --no-cache-dir "httpcore>=1.0.0" --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org

# Install the rest from requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    --default-timeout=500 --retries 10 \
    --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
