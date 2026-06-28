# Analytics MCP

**One-click GA4 + GTM analytics automation for developers, agencies, and AI agents.**

[![Tests](https://github.com/abhishekshankar/MCP-Metrics/actions/workflows/ci.yml/badge.svg)](https://github.com/abhishekshankar/MCP-Metrics/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Automate Google Analytics 4 and Google Tag Manager setup, apply opinionated tracking blueprints, monitor health, and manage everything via CLI, REST API, MCP tools, or Web UI.

**[Features](#features)** • **[Quickstart](#quickstart)** • **[Screenshots](#screenshots)** • **[CLI](#cli-commands)** • **[MCP](#mcp-client-setup)** • **[API](#rest-api)**

---

## Features

| Feature | Description |
|---------|-------------|
| **GA4 Automation** | Create properties, web data streams, optional BigQuery export |
| **GTM Automation** | Containers, GA4 config tags, event tags, publish & snippets |
| **Tracking Blueprints** | SaaS, ecommerce, and content presets with dataLayer specs |
| **Consent Presets** | none, basic, and advanced consent-gated triggers |
| **Multi-Environment** | Separate dev/stage/prod configurations |
| **Governance** | Audit log, GTM diff, rollback |
| **Health Monitoring** | Scheduled checks, webhook/email alerts, time-series charts |
| **MCP Integration** | 5 tools for Claude, Gemini, and other MCP clients |
| **Web Dashboard** | Create, monitor, and manage sites visually with charts |
| **Security** | KMS/Secrets Manager support (AWS, GCP, Azure) |
| **Reliability** | Automatic retry with exponential backoff for API calls |

---

## Quickstart

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local dev)
- Google Cloud service account with GA4 Admin, GTM, and (optional) BigQuery permissions

### 1. Clone and configure

```bash
git clone https://github.com/abhishekshankar/MCP-Metrics.git
cd MCP-Metrics
cp config/env.example .env
# Edit .env with your GTM account ID and credentials path
```

### 2. Start services

```bash
docker compose up -d
```

API available at http://localhost:8000 — health check:
```bash
curl http://localhost:8000/health
```

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

### 4. Web UI

```bash
cd web-ui && npm install && npm run dev
```

Open http://localhost:5173

---

## Screenshots

### Dashboard
List all your analytics setups with health status at a glance.

```
┌─────────────────────────────────────────────────────────────┐
│  Sites Dashboard                                            │
├──────────────┬──────────┬─────┬──────────┬────────┬────────┤
│ Domain       │ Name     │ Env │ Blueprint│ GTM    │ Status │
├──────────────┼──────────┼─────┼──────────┼────────┼────────┤
│ example.com  │ Example  │ prod│ saas     │ GTM-ABC│ active │
│ shop.com     │ Shop     │ prod│ ecommerce│ GTM-DEF│ active │
│ blog.com     │ Blog     │ prod│ content  │ GTM-GHI│ active │
└──────────────┴──────────┴─────┴──────────┴────────┴────────┘
```

### Site Detail with Health Charts
View detailed health metrics with time-series charts showing events, sessions, and conversions over time.

```
┌─────────────────────────────────────────────────────────────┐
│  example.com · prod                                         │
├─────────────────────────────────────────────────────────────┤
│  G-XXXXXXXX  │  GTM-XXXX  │  saas  │  healthy              │
├─────────────────────────────────────────────────────────────┤
│  Health Metrics (24h)                                         │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Events: 1,500  │  Sessions: 800  │  Conversions: 45  ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Health Trends (30 Days)                                    │
│  ═══════════════════════════════════════════════════════    │
│  ║  Chart: Events & Sessions over time                    ║    │
│  ║  Chart: Conversions bar chart                           ║    │
│  ═══════════════════════════════════════════════════════    │
│                                                             │
│  GTM Configuration Diff                                     │
│  ├─ Tags: +3 added, -1 removed                              │
│  ├─ Triggers: +2 added                                     │
│  └─ Variables: no changes                                  │
└─────────────────────────────────────────────────────────────┘
```

### Blueprint Editor
View, edit, and create custom tracking blueprints with live validation.

```
┌─────────────────────────────────────────────────────────────┐
│  Blueprint Editor                                           │
│  [saas] [ecommerce] [content] [+ New Blueprint]             │
├─────────────────────────────────────────────────────────────┤
│  name: saas                                                 │
│  description: SaaS product site tracking                   │
│  events:                                                    │
│    - signup_started                                         │
│    - signup_completed                                       │
│    - trial_started                                          │
│    - pricing_view                                           │
│                                                             │
│  [Apply to Site]  [Save Changes]                            │
└─────────────────────────────────────────────────────────────┘
```

---

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

---

## MCP Client Setup

### Claude Desktop

Copy `config/mcp-claude.example.json` into your Claude Desktop MCP config:

```json
{
  "mcpServers": {
    "analytics": {
      "command": "python",
      "args": ["/path/to/analytics_mcp_mcp_server.py"],
      "env": {
        "DATABASE_URL": "postgresql://..."
      }
    }
  }
}
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `create_analytics_setup` | Create GA4 + GTM setup for a new site |
| `get_analytics_status` | Get current status of a site's analytics |
| `apply_tracking_blueprint` | Apply a tracking blueprint to a site |
| `describe_analytics_setup` | Get human-readable description of setup |
| `get_health_status` | Get health status with metrics |

---

## REST API

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health |
| POST | `/sites` | Create site |
| GET | `/sites` | List sites |
| GET | `/sites/:domain` | Site status |
| POST | `/sites/:domain/blueprint` | Apply blueprint |
| GET | `/sites/:domain/health` | Health check |
| GET | `/sites/:domain/health/history` | Health history (charts data) |
| GET | `/sites/:domain/versions` | Blueprint version history |
| GET | `/sites/:domain/diff` | GTM config diff |
| POST | `/sites/:domain/rollback` | Rollback |
| GET | `/audit` | Audit log |
| POST | `/blueprints/:name` | Save custom blueprint |

OpenAPI docs: http://localhost:8000/docs

### Authentication

Pass `X-API-Key` header with admin or readonly key (configured in `.env`):

```bash
curl -H "X-API-Key: admin-key-change-me" http://localhost:8000/sites
```

---

## Architecture

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│    CLI      │  │   Web UI    │  │  MCP Client │
│   (Typer)   │  │  (React)    │  │   (FastMCP) │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
              ┌─────────▼──────────┐
              │   FastAPI REST     │
              │  + MCP Server      │
              └─────────┬──────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼───────┐ ┌─────▼─────┐ ┌──────▼──────┐
│  GA4Service   │ │ GTMService│ │HealthService│
│  (w/ retry)   │ │ (w/ retry)│ │(w/ scheduler)│
└───────┬───────┘ └─────┬─────┘ └──────┬──────┘
        │               │              │
        └───────────────┼──────────────┘
                        │
        ┌───────────────▼───────────────┐
        │    Google APIs (GA4, GTM, BQ) │
        └───────────────────────────────┘
                        │
               ┌────────▼────────┐
               │   PostgreSQL    │
               │  (Sites, Audit)  │
               └─────────────────┘
```

---

## Security Features

### KMS/Secrets Manager Support

Store Google service account credentials securely:

```bash
# AWS Secrets Manager
KMS_PROVIDER=aws
AWS_SECRET_NAME=analytics-mcp/google-credentials

# GCP Secret Manager
KMS_PROVIDER=gcp
GOOGLE_CLOUD_PROJECT=your-project

# Azure Key Vault
KMS_PROVIDER=azure
AZURE_KEY_VAULT_URL=https://your-vault.vault.azure.net/
AZURE_SECRET_NAME=google-credentials
```

### API Authentication

- Admin and read-only API keys
- Role-based access control
- Audit logging of all operations

---

## Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
MOCK_GOOGLE_APIS=true pytest backend/tests -v

# Run API locally
DATABASE_URL=postgresql://analytics:analytics@localhost:5432/analytics_mcp \
MOCK_GOOGLE_APIS=true \
PYTHONPATH=backend/src uvicorn main:app --reload

# Run migrations
alembic -c backend/alembic.ini upgrade head

# Web UI development
cd web-ui && npm install && npm run dev
```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MOCK_GOOGLE_APIS` | Use mock Google APIs (no real credentials needed) | `true` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | - |
| `GTM_ACCOUNT_ID` | GTM account ID | `1234567` |
| `KMS_PROVIDER` | Secrets manager (aws/gcp/azure) | - |
| `API_RETRY_ATTEMPTS` | Number of retry attempts for API calls | `3` |
| `HEALTH_CHECK_INTERVAL_MINUTES` | Health check scheduler interval | `60` |

See `config/env.example` for full configuration options.

---

## Mock Mode

Set `MOCK_GOOGLE_APIS=true` (default in docker-compose) to run without real Google credentials. All GA4/GTM operations use in-memory mocks — ideal for development and CI.

---

## Contributing

Contributions welcome! Please read our contributing guidelines (coming soon).

---

## License

MIT — see [LICENSE](LICENSE)
