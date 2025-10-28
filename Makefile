.PHONY: qa
qa:
	ruff format --check
	ruff check
	pytest --cov=src --cov=tests --cov-report=term-missing
	mypy src/hotpass/pipeline/config.py scripts/quality/fitness_functions.py
	bandit -r src scripts
	python -m detect_secrets scan src tests scripts
	pre-commit run --all-files --show-diff-on-failure

EXTRAS ?= dev orchestration

.PHONY: sync
sync:
	@echo "Synchronising extras: $(EXTRAS)"
	@HOTPASS_UV_EXTRAS="$(EXTRAS)" bash scripts/uv_sync_extras.sh
