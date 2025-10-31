.PHONY: qa
qa:
	ruff format --check
	ruff check
	pytest --cov=apps/data-platform --cov=tests --cov-report=term-missing
	mypy apps/data-platform/hotpass/pipeline/config.py apps/data-platform/hotpass/pipeline/orchestrator.py ops/quality/fitness_functions.py
	bandit -r apps/data-platform ops
	python -m detect_secrets scan apps/data-platform tests ops
	pre-commit run --all-files --show-diff-on-failure

EXTRAS ?= dev orchestration
MARQUEZ_API_PORT ?= 5000
MARQUEZ_UI_PORT ?= 3000

.PHONY: sync
sync:
	@echo "Synchronising extras: $(EXTRAS)"
	@HOTPASS_UV_EXTRAS="$(EXTRAS)" bash ops/uv_sync_extras.sh

.PHONY: semgrep-auto
semgrep-auto:
	@HOTPASS_CA_BUNDLE_B64="$(HOTPASS_CA_BUNDLE_B64)" bash ops/security/semgrep_auto.sh

.PHONY: marquez-up
marquez-up:
	@command -v docker >/dev/null 2>&1 || (echo "Docker CLI is required to start Marquez" >&2 && exit 1)
	@docker info >/dev/null 2>&1 || (echo "Docker daemon must be running to start Marquez" >&2 && exit 1)
	@if lsof -i tcp:$(MARQUEZ_API_PORT) >/dev/null 2>&1; then \
		echo "Port $(MARQUEZ_API_PORT) is already in use; set MARQUEZ_API_PORT to an open port" >&2; \
		exit 1; \
	fi
	@if lsof -i tcp:$(MARQUEZ_UI_PORT) >/dev/null 2>&1; then \
		echo "Port $(MARQUEZ_UI_PORT) is already in use; set MARQUEZ_UI_PORT to an open port" >&2; \
		exit 1; \
	fi
	@MARQUEZ_API_PORT=$(MARQUEZ_API_PORT) MARQUEZ_UI_PORT=$(MARQUEZ_UI_PORT) docker compose -f infra/marquez/docker-compose.yaml up -d

.PHONY: marquez-down
marquez-down:
	@command -v docker >/dev/null 2>&1 || (echo "Docker CLI is required to stop Marquez" >&2 && exit 1)
	@docker info >/dev/null 2>&1 || (echo "Docker daemon must be running to stop Marquez" >&2 && exit 1)
	@MARQUEZ_API_PORT=$(MARQUEZ_API_PORT) MARQUEZ_UI_PORT=$(MARQUEZ_UI_PORT) docker compose -f infra/marquez/docker-compose.yaml down
