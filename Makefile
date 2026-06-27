QUERY ?= Bosch 500 series dishwasher
CRON ?= 0 8 * * *
IMAGE ?= deal-hunter:latest
REGISTRY ?= quay.io/rh-demos

.PHONY: setup run run-mock run-schedule app test lint build run-container push deploy undeploy clean help

# ---------- Development ----------

setup: ## Install dependencies
	uv sync

run: ## Run the agent (requires SERPAPI_KEY and LLM endpoint)
	uv run python -m deal_hunter "$(QUERY)"

run-mock: ## Run with mock data (no API keys needed)
	USE_MOCK_DATA=true uv run python -m deal_hunter --non-interactive "$(QUERY)"

run-interactive: ## Run with mock data in interactive mode
	USE_MOCK_DATA=true uv run python -m deal_hunter "$(QUERY)"

app: ## Launch the web UI (chat + agent trace)
	uv run python -m deal_hunter.app

run-schedule: ## Run on a local cron schedule
	uv run python -m deal_hunter --schedule "$(CRON)" "$(QUERY)"

test: ## Run tests
	uv run pytest tests/ -v

lint: ## Lint and format check
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

format: ## Auto-format code
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

# ---------- Container ----------

build: ## Build the container image with Podman
	podman build -t $(IMAGE) -f Containerfile .

run-container: ## Run the agent in a Podman container
	podman run --rm \
		-v ./reports:/app/reports:Z \
		--env-file .env \
		$(IMAGE) "$(QUERY)"

push: ## Push container image to registry
	podman tag $(IMAGE) $(REGISTRY)/$(IMAGE)
	podman push $(REGISTRY)/$(IMAGE)

# ---------- OpenShift AI ----------

deploy: ## Deploy to OpenShift AI
	oc apply -k deploy/openshift/

undeploy: ## Remove from OpenShift
	oc delete -k deploy/openshift/

# ---------- Cleanup ----------

clean: ## Remove generated files
	rm -rf reports/ price_history.db

# ---------- Help ----------

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'
