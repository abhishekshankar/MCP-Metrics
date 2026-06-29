# MCP-Metrics Installation Guide

One-click GA4 + GTM analytics automation with MCP (Model Context Protocol) integration.

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/abhi/MCP-Metrics.git
cd MCP-Metrics
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```bash
# Required: API Security (generate strong random values)
API_SECRET_KEY=$(openssl rand -hex 32)
ADMIN_API_KEY=$(openssl rand -hex 16)
READONLY_API_KEY=$(openssl rand -hex 16)

# Database (default works with docker-compose)
DATABASE_URL=postgresql+psycopg2://analytics:analytics@localhost:5433/analytics_mcp

# Google Cloud (only needed for production - mock mode works without these)
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
# GOOGLE_CLOUD_PROJECT=your-project-id

# Mock Mode (set to "true" for development without Google credentials)
MOCK_GOOGLE_APIS=true

# GTM Account (default is fine for mock mode)
GTM_ACCOUNT_ID=1234567
```

### 3. Start Services

Using Docker (recommended):

```bash
docker-compose up -d
```

Services will be available at:
- **Web UI**: http://localhost:5173
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 4. Verify Installation

```bash
# Check API health
curl http://localhost:8000/health

# Expected response:
# {"status":"ok","database":"ok","service":"analytics-mcp"}
```

## Claude Code MCP Integration

To use MCP-Metrics as an MCP tool in Claude Code:

### Option A: FastMCP Server (stdio)

Add to your Claude Code settings:

```json
{
  "mcpServers": {
    "analytics-mcp": {
      "command": "python",
      "args": [
        "-m",
        "mcp.server"
      ],
      "env": {
        "DATABASE_URL": "postgresql+psycopg2://analytics:analytics@localhost:5433/analytics_mcp",
        "MOCK_GOOGLE_APIS": "true",
        "API_SECRET_KEY": "your-secret-key"
      },
      "workingDir": "/path/to/MCP-Metrics/backend/src"
    }
  }
}
```

### Option B: REST API via HTTP

If Claude Code supports HTTP MCP servers:

```json
{
  "mcpServers": {
    "analytics-mcp": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "X-API-Key": "your-admin-api-key"
      }
    }
  }
}
```

## Available MCP Tools

Once connected, Claude can use these tools:

| Tool | Description |
|------|-------------|
| `create_analytics_setup` | Create GA4 + GTM setup for a domain |
| `get_analytics_status` | Check status and health of a site |
| `apply_tracking_blueprint` | Apply SaaS/Ecommerce/Content blueprint |
| `describe_analytics_setup` | Get human-readable setup description |
| `get_health_status` | Get health metrics and anomaly flags |
| `search_ga4_schema` | Search GA4 dimensions/metrics |
| `query_ga4_data` | Query analytics data |
| `verify_gtm_preview` | Verify GTM Preview mode before publishing |
| `analyze_site_structure` | Crawl and analyze website structure |
| **Browser Controller Tools** ||
| `run_browser_test` | Run automated browser tests with actions |
| `test_mcp_metrics_app` | Test MCP-Metrics application automatically |
| `create_site_via_ui` | Create site using Web UI automation |
| `browser_gtm_preview_test` | Test GTM Preview in real browser |
| `crawl_website` | Crawl and map website structure |

## Development Setup (without Docker)

### Backend

```bash
cd backend
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+psycopg2://analytics:analytics@localhost:5433/analytics_mcp"
export MOCK_GOOGLE_APIS="true"
export API_SECRET_KEY="dev-secret"
export ADMIN_API_KEY="admin-key"
export READONLY_API_KEY="readonly-key"

# Run migrations
alembic upgrade head

# Start API
PYTHONPATH=src uvicorn main:app --reload --port 8000
```

### Web UI

```bash
cd web-ui
npm install
npm run dev
```

### Playwright (for site analyzer)

```bash
# Required for site crawling and GTM preview verification
playwright install chromium
```

## Production Deployment

### Required Changes

1. **Set `MOCK_GOOGLE_APIS=false`** - Use real Google APIs
2. **Configure Google credentials** - Set `GOOGLE_APPLICATION_CREDENTIALS`
3. **Use strong API keys** - Generate cryptographically random keys
4. **Enable HTTPS** - Use TLS for all endpoints
5. **Set up KMS** - Use AWS/GCP/Azure for secret management

### Environment for Production

```bash
# Required
API_SECRET_KEY=<strong-random-64-char-hex>
ADMIN_API_KEY=<strong-random-32-char-hex>
READONLY_API_KEY=<strong-random-32-char-hex>
MOCK_GOOGLE_APIS=false
GOOGLE_APPLICATION_CREDENTIALS=/secure/path/to/credentials.json
GOOGLE_CLOUD_PROJECT=your-gcp-project-id

# Optional: KMS for credential management
KMS_PROVIDER=aws  # or gcp, azure
AWS_REGION=us-east-1
AWS_SECRET_NAME=google-service-account-json

# Database
DATABASE_URL=postgresql+psycopg2://user:pass@prod-db-host:5432/analytics_mcp
```

## Troubleshooting

### Port Conflicts

If ports are already in use:

```bash
# Edit docker-compose.yml to change ports:
ports:
  - "8001:8000"  # API on 8001
  - "5434:5432"  # DB on 5434
```

### Database Connection Issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

### Google API Errors (Production)

Ensure:
1. Service account has GA4 Admin and GTM Editor permissions
2. Billing is enabled on GCP project
3. APIs are enabled (Analytics Admin API, Tag Manager API)

## Testing

```bash
# Backend tests
cd backend
MOCK_GOOGLE_APIS=true \
API_SECRET_KEY=test \
ADMIN_API_KEY=test-admin \
READONLY_API_KEY=test-readonly \
pytest tests/ -v

# TypeScript type check
cd web-ui
npx tsc --noEmit
```

## Support

- GitHub Issues: https://github.com/abhi/MCP-Metrics/issues
- API Docs: http://localhost:8000/docs (when running)
