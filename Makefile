.PHONY: install test run run-dev

install:
	uv pip install -r app/requirements.txt

test:
	pytest

run:
	PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000

run-dev:
	PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

infra-dev:
	export DOCKER_API_VERSION=1.41 && docker compose -f docker-compose.dev.yml up --build

infra:
	export DOCKER_API_VERSION=1.41 && docker compose -f docker-compose.yml up -d --build