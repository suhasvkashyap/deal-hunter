# Deal Hunter: AI-Powered Price Comparison Agent

An agentic AI application that compares product prices across Amazon, Costco, Walmart, and Best Buy. Built with LangGraph, local LLMs, and Podman -- designed to run on your laptop and scale to OpenShift AI.

## What It Does

1. You tell the agent what product you want (e.g., "Bosch 800 series dishwasher")
2. The agent searches multiple retailers via Google Shopping
3. It compares prices, shipping, warranties, and installation perks
4. It generates a comparison report with a clear recommendation

The agent highlights things you would miss shopping on your own:
- Costco includes free installation and old appliance disposal (saves ~$190 vs Amazon)
- Best Buy offers 0% financing for 12 months on purchases over $799
- Walmart's return window is 30 days vs Costco's 90 days
- Costco extends the manufacturer warranty from 1 year to 2 years

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Agent orchestration | **LangGraph** | State machine with nodes for search, confirm, analyze, report |
| LLM | **Ollama / vLLM / OpenAI** | Any OpenAI-compatible endpoint (default: Gemma3 4B on Ollama) |
| Search data | **SerpAPI** (Google Shopping) | Product search across retailers, with mock data fallback |
| Web UI | **Gradio** | Chat interface with live agent trace panel |
| Data models | **Pydantic** | Product, PricePoint, Perk schemas |
| Price history | **SQLite** | Track price changes over time |
| Scheduling | **APScheduler** / K8s CronJob | Run comparisons on a recurring schedule |
| Container | **Podman** + Red Hat **UBI 9** | Rootless container, OpenShift-compatible |
| Deployment | **OpenShift AI** + **vLLM** via KServe | GPU-accelerated model serving at scale |
| Package manager | **uv** | Fast Python dependency management |

## Architecture

```
                         +------------------+
                         |    User Query     |
                         | "Bosch dishwasher"|
                         +--------+---------+
                                  |
                    +-------------v--------------+
                    |     Gradio Web UI / CLI     |
                    +-------------+--------------+
                                  |
              +-------------------v--------------------+
              |           LangGraph Agent              |
              |                                        |
              |  +----------+    +-----------------+   |
              |  | Searcher +--->| Confirmer /     |   |
              |  | (SerpAPI)|    | Auto-Confirm    |   |
              |  +----------+    +--------+--------+   |
              |                           |            |
              |                  +--------v--------+   |
              |                  |    Analyzer      |   |
              |                  | (prices, perks)  |   |
              |                  +--------+--------+   |
              |                           |            |
              |                  +--------v--------+   |
              |                  |    Reporter      |   |
              |                  |  (LLM analysis)  |   |
              |                  +-----------------+   |
              +----------------------------------------+
                        |                |
              +---------v---+    +-------v--------+
              |   SQLite    |    | Markdown Report |
              | (history)   |    |   (output)      |
              +-------------+    +----------------+

         +--------------------------------------------+
         |          Deployment Options                 |
         |                                            |
         |  Local        Container       OpenShift AI  |
         |  python -m    podman run      CronJob +     |
         |  deal_hunter  deal-hunter     vLLM serving  |
         +--------------------------------------------+
```

**Searcher**: Queries Google Shopping via SerpAPI, filters results by retailer. Falls back to bundled mock data when no API key is set.

**Confirmer / Auto-Confirm**: In interactive mode (CLI), presents found products for user selection. In headless mode (web UI, scheduled runs), auto-selects the top result per retailer.

**Analyzer**: Fetches current prices, perks (installation, warranty, disposal, membership), and saves to SQLite for historical tracking.

**Reporter**: Sends product data to the LLM for comparison analysis. Focuses on non-obvious considerations like total cost of ownership, hidden fees, and retailer-specific benefits.

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- [Ollama](https://ollama.com/) with a model pulled

### 1. Clone and setup

```bash
git clone https://github.com/sukashyar/deal-hunter.git
cd deal-hunter
make setup
```

### 2. Pull an LLM

```bash
ollama pull gemma3:4b
```

### 3. Configure (optional)

```bash
cp .env.example .env
```

Edit `.env` to set your preferences. The defaults work out of the box with Ollama and mock data.

To enable live search, get a free API key from [SerpAPI](https://serpapi.com) (100 searches/month free) and set `SERPAPI_KEY` in `.env`.

### 4. Run

**Web UI (recommended for demos):**

```bash
make app
```

Opens a browser at `http://localhost:7860` with a chat interface and live agent activity trace.

**CLI with mock data (no API keys needed):**

```bash
make run-mock QUERY="Bosch 500 series dishwasher"
```

**CLI interactive mode:**

```bash
make run-interactive QUERY="Bosch 500 series dishwasher"
```

### 5. Run in a container (Podman)

```bash
make build
make run-container QUERY="Bosch 500 series dishwasher"
```

Reports are persisted to `./reports/` via a volume mount.

### 6. Run on a schedule

```bash
make run-schedule CRON="0 8 * * *" QUERY="Bosch 500 series dishwasher"
```

### 7. Deploy to OpenShift AI

```bash
# Edit the secret with your SerpAPI key
vi deploy/openshift/agent-secret.yaml

# Deploy
make deploy
```

This deploys:
- A vLLM model server on GPU via KServe
- A CronJob that runs the agent daily
- Reports stored on a PersistentVolumeClaim

## Configuration

All settings are controlled via environment variables or a `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | `ollama`, `vllm`, or `openai` |
| `LLM_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible API endpoint |
| `LLM_MODEL` | `gemma3:4b` | Model name |
| `LLM_API_KEY` | `no-key` | API key (not needed for local models) |
| `SERPAPI_KEY` | *(none)* | SerpAPI key; if empty, uses mock data |
| `USE_MOCK_DATA` | `false` | Force mock data even if SERPAPI_KEY is set |
| `OUTPUT_DIR` | `reports` | Where to save Markdown reports |
| `RETAILERS` | `amazon,costco,walmart,bestbuy` | Comma-separated retailer list |

> **Note:** Never commit your `.env` file. It is listed in `.gitignore`. Use `.env.example` as a template.

## Available Make Targets

| Command | Description |
|---------|-------------|
| `make setup` | Install dependencies |
| `make app` | Launch the web UI (chat + agent trace) |
| `make run` | Run the agent via CLI |
| `make run-mock` | Run with mock data (no API keys needed) |
| `make run-interactive` | Run in interactive mode (select products) |
| `make run-schedule` | Run on a local cron schedule |
| `make build` | Build the container image with Podman |
| `make run-container` | Run the agent in a Podman container |
| `make deploy` | Deploy to OpenShift AI |
| `make test` | Run tests |
| `make lint` | Lint and format check |
| `make help` | Show all available targets |

## Project Structure

```
deal-hunter/
├── src/deal_hunter/
│   ├── __main__.py           # CLI entry point
│   ├── app.py                # Gradio web UI
│   ├── config.py             # Environment-based configuration
│   ├── models.py             # Product, PricePoint, Perk data models
│   ├── trace.py              # Agent activity trace logger
│   ├── graph/                # LangGraph agent orchestration
│   │   ├── state.py          # Agent state schema
│   │   ├── builder.py        # Graph construction
│   │   ├── edges.py          # Conditional routing
│   │   └── nodes/            # Searcher, Confirmer, Analyzer, Reporter
│   ├── search/               # SerpAPI + mock data clients
│   ├── llm/                  # LLM provider factory
│   ├── storage/              # SQLite price history
│   ├── reporting/            # Markdown report builder
│   └── scheduler/            # APScheduler for local cron
├── mock_data/                # Pre-built JSON for offline demos
├── deploy/openshift/         # Kubernetes/OpenShift manifests
├── Containerfile             # Multi-stage build with UBI 9
├── Makefile                  # All demo commands
└── .env.example              # Configuration template
```

## Red Hat Technologies

This demo highlights several Red Hat-backed technologies:

- **Podman** -- Rootless container runtime, no Docker daemon needed
- **Red Hat UBI 9** -- Enterprise container base image, free to redistribute
- **OpenShift AI** -- ML platform for deploying models and agents at scale
- **vLLM on KServe** -- High-performance model serving with OpenAI-compatible API
- **Granite** -- IBM/Red Hat open-source LLM family

## License

Apache-2.0
