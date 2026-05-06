FROM python:3.12-slim

WORKDIR /app

COPY moderation-consumer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common ./common
COPY moderation-consumer/app ./app
COPY moderation-consumer/tests ./tests
COPY moderation-consumer/pytest.ini .

EXPOSE 9443
