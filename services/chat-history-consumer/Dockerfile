FROM python:3.12-slim

WORKDIR /app

COPY chat-history-consumer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common ./common
COPY chat-history-consumer/app ./app
COPY chat-history-consumer/tests ./tests
COPY chat-history-consumer/pytest.ini .

EXPOSE 9443
