# Convenience targets. Run `make help` for a list.
.DEFAULT_GOAL := help
ML_VENV := ml/.venv
ML_BIN := $(ML_VENV)/bin

.PHONY: help
help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

.env:
	cp .env.example .env

.PHONY: up
up: .env ## Build and start the full stack (UI on http://localhost:3000)
	docker compose up --build -d

.PHONY: down
down: ## Stop the stack (keeps the database volume)
	docker compose down

.PHONY: reset
reset: ## Stop the stack and delete the demo database volume
	docker compose down -v

.PHONY: logs
logs: ## Follow logs of all services
	docker compose logs -f

$(ML_BIN)/tlp-ml:
	python3 -m venv $(ML_VENV)
	$(ML_BIN)/pip install -e "./ml[dev]"

.PHONY: ml-setup
ml-setup: $(ML_BIN)/tlp-ml ## Create the Python virtualenv for the ML package

.PHONY: ml-train
ml-train: ml-setup ## Generate synthetic data, run EDA, train and evaluate the model
	$(ML_BIN)/tlp-ml generate-data
	$(ML_BIN)/tlp-ml eda
	$(ML_BIN)/tlp-ml train

.PHONY: test
test: test-backend test-ml test-frontend ## Run all test suites

.PHONY: test-backend
test-backend: ## Backend tests (needs Docker for Testcontainers)
	cd backend && mvn -B verify

.PHONY: test-ml
test-ml: ml-setup ## ML tests and lint
	cd ml && .venv/bin/ruff check src tests && .venv/bin/pytest

.PHONY: test-frontend
test-frontend: ## Frontend tests and production build
	cd frontend && npm ci && npm test && npm run build
