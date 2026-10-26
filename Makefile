COMPOSE = docker compose -f deploy/docker-compose.yml --env-file .env

.PHONY: install check check-all fmt up down logs

install:
	uv sync

check:
	uv run ruff check .
	uv run ruff format --check .
	uv run pytest

check-all: check
	uv run pytest -m integration

fmt:
	uv run ruff check --fix .
	uv run ruff format .

up:
	$(COMPOSE) up -d --wait

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f litellm
