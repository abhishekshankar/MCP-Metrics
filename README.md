# Analytics MCP

**One-click GA4 + GTM analytics automation for developers, agencies, and AI agents.**

Automate Google Analytics 4 and Google Tag Manager setup, apply opinionated tracking blueprints, monitor health, and manage everything via CLI, REST API, MCP tools, or Web UI.

## Features

- **GA4 Automation** — Create properties, web data streams, optional BigQuery export
- **GTM Automation** — Containers, GA4 config tags, event tags, publish & snippets
- **Tracking Blueprints** — SaaS, ecommerce, and content presets with dataLayer specs
- **Consent Presets** — none, basic, and advanced consent-gated triggers
- **Multi-Environment** — Separate dev/stage/prod configurations
- **Governance** — Audit log, GTM diff, rollback
- **Health Monitoring** — Scheduled checks, webhook/email alerts
- **MCP Integration** — 5 tools for Claude, Gemini, and other MCP clients
- **Web Dashboard** — Create, monitor, and manage sites visually

## Quickstart

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local dev)
- Google Cloud service account with GA4 Admin, GTM, and (optional) BigQuery permissions

### 1. Clone and configure

```bash
git clone https://github.com/your-org/analytics-mcp.git
cd analytics-mcp
cp config/env.example .env
# Edit .env with your GTM account ID and credentials path
```

### 2. Start services

```bash
docker compose up -d
```

API available at http://localhost:8000 — health check: `curl http://localhost:8000/health`

### 3. Create your first site

```bash
pip install -e ".[dev]"
analytics-mcp create \
  --domain example.com \
  --name "Example Site" \
  --env prod \
  --blueprint saas \
  --pretty
```

### 4. Web UI (optional)

```bash
cd web-ui && npm install && npm run dev
```

Open http://localhost:5173

## CLI Commands

| Command | Description |
|---------|-------------|
| `analytics-mcp create` | Full GA4 + GTM + blueprint setup |
| `analytics-mcp status` | Get site status |
| `analytics-mcp list` | List all sites |
| `analytics-mcp apply-blueprint` | Apply/update blueprint |
| `analytics-mcp health` | Run health check |
| `analytics-mcp rollback` | Rollback GTM version |
| `analytics-mcp describe` | Human-readable setup summary |

## MCP Client Setup

### Claude Desktop

Copy `config/mcp-claude.example.json` into your Claude Desktop MCP config.

### Gemini CLI

```bash
source config/gemini-fastmcp.example.sh
```

## REST API

- `GET /health` — Service health
- `POST /sites` — Create site
- `GET /sites` — List sites
- `GET /sites/:domain` — Site status
- `POST /sites/:domain/blueprint` — Apply blueprint
- `GET /sites/:domain/health` — Health check
- `POST /sites/:domain/rollback` — Rollback
- `GET /audit` — Audit log

OpenAPI docs: http://localhost:8000/docs

### Authentication

Pass `X-API-Key` header with admin or readonly key (configured in `.env`).

## Architecture

```
CLI / MCP / Web UI → FastAPI → Services → Google APIs (GA4, GTM, BigQuery)
                                    ↓
                               PostgreSQL
```

## Development

```bash
# Install
pip install -e ".[dev]"

# Run tests
MOCK_GOOGLE_APIS=true pytest backend/tests -v

# Run API locally
DATABASE_URL=postgresql://analytics:analytics@localhost:5432/analytics_mcp \
MOCK_GOOGLE_APIS=true \
PYTHONPATH=backend/src uvicorn main:app --reload

# Migrations
alembic -c backend/alembic.ini upgrade head
```

## Mock Mode

Set `MOCK_GOOGLE_APIS=true` to run without real Google credentials. All GA4/GTM operations use in-memory mocks — ideal for development and CI.

## License

MIT — see [LICENSE](LICENSE)
