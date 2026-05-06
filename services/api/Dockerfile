FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common ./common
COPY api/app ./app
COPY api/tests ./tests
COPY api/pytest.ini .

EXPOSE 8443
