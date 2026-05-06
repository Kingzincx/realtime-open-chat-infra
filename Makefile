CERT_FILES=certs/ca.crt certs/nginx.crt certs/nginx.key certs/api.crt certs/api.key certs/event-consumer.crt certs/event-consumer.key certs/chat-history-consumer.crt certs/chat-history-consumer.key certs/moderation-consumer.crt certs/moderation-consumer.key
SECRET_FILES=secrets/postgres_password.txt secrets/grafana_admin_password.txt secrets/airflow_admin_password.txt secrets/airflow_postgres_password.txt

.PHONY: certs ensure-certs secrets ensure-secrets up down logs build restart ps test lint clean

certs:
	chmod +x scripts/generate-certs.sh
	./scripts/generate-certs.sh

secrets:
	chmod +x scripts/generate-secrets.sh
	./scripts/generate-secrets.sh

ensure-certs:
	@if [ ! -f certs/ca.crt ] || [ ! -f certs/nginx.crt ] || [ ! -f certs/nginx.key ] || [ ! -f certs/api.crt ] || [ ! -f certs/api.key ] || [ ! -f certs/event-consumer.crt ] || [ ! -f certs/event-consumer.key ] || [ ! -f certs/chat-history-consumer.crt ] || [ ! -f certs/chat-history-consumer.key ] || [ ! -f certs/moderation-consumer.crt ] || [ ! -f certs/moderation-consumer.key ]; then \
		echo "Local TLS certificates are missing. Generating them now..."; \
		$(MAKE) certs; \
	fi

ensure-secrets:
	@if [ ! -f secrets/postgres_password.txt ] || [ ! -f secrets/grafana_admin_password.txt ] || [ ! -f secrets/airflow_admin_password.txt ] || [ ! -f secrets/airflow_postgres_password.txt ]; then \
		echo "Local secret files are missing. Generating them now..."; \
		$(MAKE) secrets; \
	fi

up: ensure-certs ensure-secrets
	docker compose up --build

down:
	docker compose down --remove-orphans

logs:
	docker compose logs -f

build: ensure-certs ensure-secrets
	docker compose build

restart: down up

ps:
	docker compose ps

test:
	docker compose run --rm --no-deps api pytest -q
	docker compose run --rm --no-deps event-consumer pytest -q
	docker compose run --rm --no-deps chat-history-consumer pytest -q
	docker compose run --rm --no-deps moderation-consumer pytest -q

lint:
	docker compose run --rm --no-deps api python -m compileall app tests
	docker compose run --rm --no-deps event-consumer python -m compileall app tests
	docker compose run --rm --no-deps chat-history-consumer python -m compileall app tests
	docker compose run --rm --no-deps moderation-consumer python -m compileall app tests

clean:
	docker compose down -v --remove-orphans
