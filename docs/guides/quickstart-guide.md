[Back to README](../../README.md)

# Quickstart Guide

> Get the Zero-Employee Orchestrator up and running, execute your first workflow, and learn the essential CLI commands.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Method 1: PyPI (Recommended)](#method-1-pypi-recommended)
  - [Method 2: From Source](#method-2-from-source)
  - [Method 3: Docker](#method-3-docker)
  - [Comparison Table](#comparison-table)
- [Configuration](#configuration)
  - [Option A: Subscription Mode (No API Key)](#option-a-subscription-mode-no-api-key)
  - [Option B: Ollama Local LLM (Fully Offline)](#option-b-ollama-local-llm-fully-offline)
  - [Option C: OpenRouter (One Key, Many Models)](#option-c-openrouter-one-key-many-models)
  - [Option D: Individual Provider Keys](#option-d-individual-provider-keys)
  - [Configuration Comparison](#configuration-comparison)
- [First Startup](#first-startup)
- [Your First Workflow](#your-first-workflow)
- [CLI Basics](#cli-basics)
- [Desktop App](#desktop-app)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Python** | 3.12 or later | Required for all installation methods |
| **Node.js** | 20 or later | Required only for the desktop app (Tauri + React) |
| **Docker** | Latest stable | Optional -- alternative installation method |
| **Rust** | Latest stable | Required only for building the desktop app from source |

Verify your environment:

```bash
python --version    # Should print 3.12+
node --version      # Should print v20+ (only needed for desktop)
docker --version    # Optional
```

---

## Installation

### Method 1: PyPI (Recommended)

The fastest way to get started. Installs ZEO as a global CLI tool.

```bash
pip install zero-employee-orchestrator
```

After installation, the `zero-employee` command is available system-wide.

### Method 2: From Source

Best for contributors or users who want the latest development version.

```bash
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
pip install .
```

For development with hot-reload and test dependencies:

```bash
pip install -e ".[dev]"
```

### Method 3: Docker

Run ZEO in an isolated container with no local Python setup required.

```bash
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
docker compose up -d
```

The API server will be available at `http://localhost:18234`.

### Comparison Table

| | PyPI | Source | Docker |
|---|---|---|---|
| **Setup time** | ~1 minute | ~2 minutes | ~3 minutes |
| **Best for** | End users | Contributors | Isolated / production deployments |
| **Auto-updates** | `pip install --upgrade` | `git pull && pip install .` | `docker compose pull && docker compose up -d` |
| **Requires Python locally** | Yes | Yes | No |
| **Hot-reload for development** | No | Yes (`pip install -e ".[dev]"`) | Via volume mounts |

---

## Configuration

ZEO does not require an API key to start. Choose the mode that fits your needs.

### Option A: Subscription Mode (No API Key)

Uses g4f to access LLMs through existing subscriptions (e.g., ChatGPT Plus, Claude Pro). No API key needed.

```bash
zero-employee config set DEFAULT_EXECUTION_MODE subscription
```

### Option B: Ollama Local LLM (Fully Offline)

Run models entirely on your machine. No internet connection or API key required.

1. Install Ollama from [ollama.com](https://ollama.com).
2. Pull a model and configure ZEO:

```bash
zero-employee config set DEFAULT_EXECUTION_MODE free
zero-employee pull qwen3:8b
```

Other recommended local models: `llama3.1:8b`, `mistral:7b`, `gemma2:9b`.

### Option C: OpenRouter (One Key, Many Models)

Access hundreds of models from multiple providers with a single API key.

1. Create an account at [openrouter.ai](https://openrouter.ai).
2. Generate an API key and configure ZEO:

```bash
zero-employee config set OPENROUTER_API_KEY <your-key>
```

### Option D: Individual Provider Keys

Set API keys for specific providers. All keys are optional -- configure only the providers you want to use.

```bash
# OpenAI (GPT series)
zero-employee config set OPENAI_API_KEY <your-key>

# Anthropic (Claude series)
zero-employee config set ANTHROPIC_API_KEY <your-key>

# Google (Gemini series -- free tier available)
zero-employee config set GEMINI_API_KEY <your-key>

# Mistral
zero-employee config set MISTRAL_API_KEY <your-key>

# DeepSeek
zero-employee config set DEEPSEEK_API_KEY <your-key>

# Cohere
zero-employee config set COHERE_API_KEY <your-key>
```

### Configuration Comparison

| Mode | API Key Required | Internet Required | Cost | Best For |
|------|:---:|:---:|------|----------|
| **Subscription** | No | Yes | Included in existing LLM subscription | Users with ChatGPT Plus, Claude Pro, etc. |
| **Ollama** | No | No | Free (runs locally) | Privacy-focused or offline usage |
| **OpenRouter** | Yes (one key) | Yes | Pay per token | Access to many models with a single account |
| **Individual keys** | Yes (per provider) | Yes | Pay per token | Direct relationship with specific providers |

> **ZEO itself is free and open source.** LLM API costs are paid directly by users to each provider. ZEO does not charge any fees or take a commission.

---

## First Startup

Start the API server:

```bash
zero-employee serve
```

The server starts on `http://localhost:18234`. You should see log output indicating that the FastAPI application is running.

To enable hot-reload during development:

```bash
zero-employee serve --reload
```

Verify the server is healthy:

```bash
zero-employee health
```

---

## Your First Workflow

### Using the CLI Chat

Start an interactive chat session:

```bash
zero-employee chat
```

ZEO understands natural language. Try the following:

```
> Create a project plan for building a landing page
```

ZEO will:

1. **Design Interview** -- Ask clarifying questions to understand your requirements.
2. **Task Orchestration** -- Break the work into a DAG of tasks with dependencies and cost estimates.
3. **Approval Gate** -- Present the plan for your approval before executing anything.
4. **Execution** -- Assign tasks to specialized AI skills (spec-writer, plan-writer, task-breakdown, etc.).
5. **Judge Layer** -- Verify each output for quality using two-stage detection.
6. **Delivery** -- Return the final result with full audit trail.

### Using the Local Chat (Ollama)

For fully offline operation with a local model:

```bash
zero-employee local --model qwen3:8b --lang en
```

### Using the REST API

Send requests directly to the API:

```bash
curl -X POST http://localhost:18234/api/v1/tickets \
  -H "Content-Type: application/json" \
  -d '{"title": "Build landing page", "description": "Create a responsive landing page with hero section and contact form"}'
```

---

## CLI Basics

The `zero-employee` command is your primary interface. Here are the essential subcommands:

| Command | Description |
|---------|-------------|
| `zero-employee serve` | Start the API server (port 18234) |
| `zero-employee serve --reload` | Start with hot-reload for development |
| `zero-employee chat` | Interactive chat session |
| `zero-employee chat --mode free` | Chat using Ollama or g4f |
| `zero-employee chat --lang en` | Chat in English |
| `zero-employee local --model <name>` | Local chat with a specific Ollama model |
| `zero-employee config list` | List all configuration settings |
| `zero-employee config set <key> <value>` | Set a configuration value |
| `zero-employee models` | List available LLM models |
| `zero-employee pull <model>` | Pull an Ollama model |
| `zero-employee health` | Check server health status |
| `zero-employee db upgrade` | Run database migrations |
| `zero-employee update` | Update ZEO to the latest version |
| `zero-employee update --check` | Check for available updates without installing |

### Database

ZEO uses **SQLite** by default for development. For production deployments, PostgreSQL is recommended:

```bash
zero-employee config set DATABASE_URL postgresql+asyncpg://user:pass@localhost:5432/zeo
zero-employee db upgrade
```

---

## Desktop App

ZEO includes a desktop application built with Tauri v2 and React. To run it in development mode:

```bash
cd apps/desktop
npm install
npm run tauri dev
```

The Vite dev server runs on `http://localhost:5173` and communicates with the API server on port 18234.

---

## Troubleshooting

### Server fails to start

**Symptom:** `zero-employee serve` exits with an error.

**Solutions:**
- Verify Python 3.12+ is installed: `python --version`
- Ensure the package is installed correctly: `pip install zero-employee-orchestrator`
- Check if port 18234 is already in use: `lsof -i :18234` (macOS/Linux) or `netstat -ano | findstr :18234` (Windows)
- Run database migrations: `zero-employee db upgrade`

### Cannot connect to Ollama

**Symptom:** Chat in free mode returns connection errors.

**Solutions:**
- Ensure Ollama is running: `ollama serve`
- Verify a model is downloaded: `ollama list`
- Pull a model if none are available: `zero-employee pull qwen3:8b`
- Check that Ollama is accessible at `http://localhost:11434`

### API key not recognized

**Symptom:** Requests fail with authentication or key-related errors.

**Solutions:**
- Confirm the key is set: `zero-employee config list`
- Re-set the key: `zero-employee config set <KEY_NAME> <your-key>`
- Verify the key is valid with the provider's dashboard
- Ensure you are not mixing up execution modes (e.g., using subscription mode but expecting a key-based provider)

### Database migration errors

**Symptom:** Schema errors or missing table warnings on startup.

**Solutions:**
- Run migrations explicitly: `zero-employee db upgrade`
- For a fresh start (development only), delete the SQLite file and re-run migrations:
  ```bash
  rm -f zeo.db
  zero-employee db upgrade
  ```

### Chat produces no output or times out

**Symptom:** The chat session hangs or returns empty responses.

**Solutions:**
- Check server health: `zero-employee health`
- Verify your LLM configuration: `zero-employee config list`
- Ensure at least one LLM provider is configured and reachable
- Check server logs for errors (look at the terminal running `zero-employee serve`)

### Port conflicts

**Symptom:** "Address already in use" error on startup.

**Solutions:**
- Stop any other process using port 18234
- Or find and kill the existing process:
  ```bash
  # macOS / Linux
  lsof -ti :18234 | xargs kill -9

  # Windows
  netstat -ano | findstr :18234
  taskkill /PID <pid> /F
  ```

### Desktop app build fails

**Symptom:** `npm run tauri dev` fails with errors.

**Solutions:**
- Ensure Node.js 20+ is installed: `node --version`
- Ensure Rust is installed: `rustc --version`
- Install frontend dependencies: `cd apps/desktop && npm install`
- Ensure the API server is running on port 18234

---

## Next Steps

- Read the [Architecture Deep Dive](architecture-guide.md) to understand the 9-layer system
- Read the [Security Guide](security-guide.md) to learn about approval gates and prompt defenses
- Explore the [USER_SETUP.md](../../USER_SETUP.md) for advanced provider and media generation configuration
- Check the [ROADMAP.md](../../ROADMAP.md) for upcoming features
