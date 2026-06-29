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
| **Tracking Blueprints** | SaaS, ecommerce, content, **Web Vitals** presets with dataLayer specs |
| **Site Analyzer** | **Playwright-based crawling** — discover pages, group by business intent, identify tracking opportunities |
| **GA4 Data Querying** | **Schema discovery** + natural language queries (like surendranb/google-analytics-mcp) |
| **Consent Presets** | none, basic, and advanced consent-gated triggers |
| **Multi-Environment** | Separate dev/stage/prod configurations |
| **Governance** | Audit log, GTM diff, rollback |
| **Health Monitoring** | Scheduled checks, webhook/email alerts, time-series charts |
| **MCP Integration** | **10 tools** for Claude, Gemini, and other MCP clients |
| **Web Dashboard** | Create, monitor, and manage sites visually with charts |
| **Security** | KMS/Secrets Manager support (AWS, GCP, Azure) |
| **Reliability** | Automatic retry with exponential backoff for API calls |

---

## Competitive Landscape

### How MCP Metrics Compares

| Project | Stars | What They Do | What MCP Metrics Adds |
|---------|-------|--------------|----------------------|
| [jtrackingai/analytics-tracking-automation](https://github.com/jtrackingai/analytics-tracking-automation) | 131 | AI-powered GA4 + GTM event tracking with site analysis | **Full property/container lifecycle** + governance + health monitoring + integrated dashboard |
| [surendranb/google-analytics-mcp](https://github.com/surendranb/google-analytics-mcp) | 222 | GA4 data querying for AI agents (read-only) | **Write/setup side** — create properties, GTM containers, blueprints via MCP |
| [owntag/gtm-cli](https://github.com/owntag/gtm-cli) | ~50 | CLI for GTM API operations | **Full platform** — GA4 + GTM + blueprints + UI + health + governance |
| [google-marketing-solutions/web-vitals-gtm-template](https://github.com/google-marketing-solutions/web-vitals-gtm-template) | 42 | GTM template for Core Web Vitals | **Integrated blueprint** — Web Vitals as first-class tracking preset |

### Key Differentiators

**vs jtrackingai/analytics-tracking-automation:**
- We have **full GA4 property creation** (they focus on event tracking within existing properties)
- We have **governance** (audit logs, GTM diff, rollback)
- We have **health monitoring** with time-series charts
- We have **integrated web dashboard** (not just CLI skill)
- We have **consent management** and **cross-domain tracking**

**vs surendranb/google-analytics-mcp:**
- They are **read/query only** — GA4 data access for analysis
- We are **write/setup focused** — create and configure GA4/GTM from scratch
- **Complementary pairing:** Use MCP Metrics to set up tracking, use their server to query results

**vs owntag/gtm-cli:**
- They provide **low-level GTM API access**
- We provide **high-level opinionated platform** — one command for full setup
- We add **GA4 integration**, **blueprints**, **health monitoring**, **web UI**

**vs Web Vitals GTM Template:**
- They provide a **GTM template gallery entry**
- We provide **Web Vitals as a blueprint** integrated into the full automation workflow
- We include **attribution data** and **debugging support** in the dataLayer

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
| **Setup & Management** |
| `create_analytics_setup` | Create GA4 + GTM setup for a new site |
| `get_analytics_status` | Get current status of a site's analytics |
| `apply_tracking_blueprint` | Apply a tracking blueprint to a site |
| `describe_analytics_setup` | Get human-readable description of setup |
| `get_health_status` | Get health status with metrics |
| **GA4 Data & Schema** |
| `search_ga4_schema` | Search dimensions/metrics by keyword (like surendranb/google-analytics-mcp) |
| `list_dimension_categories` | List all GA4 dimension categories |
| `list_metric_categories` | List all GA4 metric categories |
| `get_dimensions_by_category` | Get dimensions organized by category |
| `get_metrics_by_category` | Get metrics organized by category |
| `query_ga4_data` | Query GA4 data with intelligent defaults and row estimation |
| **Verification & Analysis** |
| `verify_gtm_preview` | Test GTM Preview mode — verify tags fire before publishing |
| `analyze_site_structure` | Crawl site to discover pages and tracking opportunities |

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
| POST | `/sites/:domain/analyze` | **Site analyzer** — crawl and analyze site structure (Playwright) |
| POST | `/sites/:domain/verify-preview` | **Preview verification** — test GTM tags before publishing |

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

# Install Playwright browsers (required for site analyzer and preview verification)
playwright install chromium

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
| `MOCK_GOOGLE_APIS` | Use mock Google APIs (no real credentials needed) | `false` ⚠️ |
| `API_SECRET_KEY` | Secret key for API security | **Required** |
| `ADMIN_API_KEY` | API key for admin access | **Required** |
| `READONLY_API_KEY` | API key for read-only access | **Required** |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | - |
| `GTM_ACCOUNT_ID` | GTM account ID | `1234567` |
| `KMS_PROVIDER` | Secrets manager (aws/gcp/azure) | - |
| `API_RETRY_ATTEMPTS` | Number of retry attempts for API calls | `3` |
| `HEALTH_CHECK_INTERVAL_MINUTES` | Health check scheduler interval | `60` |

See `config/env.example` for full configuration options.

---

## Mock Mode (Development Only)

Set `MOCK_GOOGLE_APIS=true` to run without real Google credentials. All GA4/GTM operations use in-memory mocks — ideal for development and CI.

**⚠️ Warning:** Mock mode defaults to `false` for production safety. When enabled, a warning is logged:  
`"MOCK_GOOGLE_APIS is enabled. Google API calls will use fake data. NOT FOR PRODUCTION."`

**docker-compose.yml already sets `MOCK_GOOGLE_APIS=true` for local development.**

---

## Contributing

Contributions welcome! Please read our contributing guidelines (coming soon).

---

## License

MIT — see [LICENSE](LICENSE)
