FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend directory into /app/backend
COPY . /app/backend

ENV PYTHONPATH=/app/backend

# The commands will be overridden in docker-compose.yml for api vs worker
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
