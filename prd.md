Below is a **complete, full‑scope PRD** for a star‑worthy, forkable “Analytics MCP” platform that automates GA4 + GTM, adds opinionated tracking, governance, monitoring, and is usable via web UI, CLI, and MCP from Claude, Gemini, Grok, Codex.

***

## 1. Product overview

**Product name**  
Analytics MCP – One‑Click Analytics Automation for GA4 + GTM + AI Agents

**Vision**  
Provide a single, open‑source platform that:

- Automates full GA4 + GTM setup for any domain.  
- Applies opinionated tracking blueprints (SaaS, ecommerce, content) with consent/privacy presets.  
- Monitors analytics health and exports data to BigQuery.  
- Exposes everything via:
  - Web UI.  
  - CLI.  
  - REST API.  
  - MCP tools usable from Claude, Gemini, Grok, Codex, and other MCP‑aware clients. [github](https://github.com/modelcontextprotocol/servers)

**Primary users**

- Developers and product teams who spin up many sites and want consistent analytics without GA4/GTM UI clicks.  
- Analytics engineers, growth teams, and agencies who want repeatable, governed tracking setups.  
- AI/agent enthusiasts who want agents to design and implement tracking via MCP.

***

## 2. Core use cases

1. **“Create analytics for a new site” in one command**
   - Input: domain, site name, environment (dev/stage/prod), blueprint type.  
   - Outcome:
     - GA4 property + web data stream.  
     - GTM container/workspaces with GA4 tags, events, triggers.  
     - GTM snippet & optional direct GA4 snippet.  
     - Tracking blueprint applied (events, parameters, consent presets, cross‑domain rules).

2. **Apply or update tracking blueprint for an existing site**
   - Input: domain, blueprint type (SaaS/ecommerce/content/custom).  
   - Outcome:
     - GA4 events + parameters created/updated.  
     - GTM tags/triggers updated, dataLayer patterns enforced.  
     - Changes tracked in audit log and version history.

3. **Monitor analytics and get alerts**
   - Input: site domain, thresholds.  
   - Outcome:
     - Automated health checks using GA4 Data API.  
     - Alerts (webhooks/email/Slack) if traffic or key conversions drop, or if tracking breaks.

4. **Enable data export and governance**
   - Input: domain, BigQuery project/dataset.  
   - Outcome:
     - GA4 BigQuery export enabled (where permissions allow).  
     - Governance features: audit log, diffs of GTM configurations, rollback to previous versions.

5. **Use from AI agents (Claude/Gemini/Grok/Codex)**
   - Agents call MCP tools:
     - `create_analytics_setup`, `apply_tracking_blueprint`, `describe_analytics_setup`, `get_health_status`.  
   - Agents can design event schemas with user and then implement them via the platform.

***

## 3. Feature set

### 3.1 GA4 setup automation

Using Google Analytics Admin API and Data API. [support.google](https://support.google.com/analytics/answer/9304153?hl=en)

**FR‑GA4‑1: Create GA4 properties**

- For each new site:
  - Create a GA4 property via `properties.create`. [developers.google](https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1alpha/properties/create)
  - Property naming convention: `<site_name> - <environment>`.  
  - Configurable time zone and currency (defaults, with override per project). [support.google](https://support.google.com/analytics/answer/9304153?hl=en)

**FR‑GA4‑2: Create web data streams**

- Create a web data stream linked to the property with the site’s domain as default URL. [developers.google](https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1alpha/properties/create)
- Capture and store Measurement ID (e.g. `G-XXXXXXX`).

**FR‑GA4‑3: Enable BigQuery export (optional)**

- If BigQuery is configured:
  - Link GA4 property to a BigQuery project/dataset for export (using Admin API & GA console automation where possible). [ortech.com](https://ortech.com.my/insights/analytics-automation-platform/)
- Store export config in platform DB.

**FR‑GA4‑4: GA4 Data API integration**

- Use GA4 Data API to:
  - Fetch event counts, conversions, and traffic metrics for health checks and reporting. [blog.bismart](https://blog.bismart.com/en/kale/google-analytics-4)

### 3.2 GTM setup and configuration

Using Google Tag Manager API. [developers.google](https://developers.google.com/tag-platform/tag-manager/api/v2/devguide)

**FR‑GTM‑1: Container lifecycle**

- For each site:
  - Create GTM container (or reuse shared containers for multi‑site setups). [developers.google](https://developers.google.com/tag-platform/tag-manager/api/v2/devguide)
  - Support environment‑specific containers (dev/stage/prod) or environment‑specific workspaces.

**FR‑GTM‑2: GA4 config tag**

- Automatically create GA4 configuration tag:
  - Use Measurement ID from GA4 stream.  
  - Trigger: All Pages. [footprintdigital.co](https://www.footprintdigital.co.uk/library/how-to-add-ga4-to-google-tag-manager-gtm/)

**FR‑GTM‑3: Event tags and dataLayer configuration**

- Implement tracking blueprints via tags and triggers:
  - Create event tags in GTM for GA4 events.  
  - Configure triggers based on URL patterns, clicks, form submissions, dataLayer events.  
- Provide a **dataLayer spec** per blueprint and optional scripts/snippets users can include on their sites.

**FR‑GTM‑4: Versioning and publishing**

- Use GTM API to:
  - Create workspaces.  
  - Save new versions.  
  - Publish containers. [measureschool](https://measureschool.com/install-google-analytics-4-with-google-tag-manager/)
- Store version IDs and publish history for rollback and diffing.

**FR‑GTM‑5: GTM snippet generation**

- Generate both `<head>` script and `<noscript>` `<body>` snippet for the container. [github](https://github.com/BuildWithLal/python-google-tag-manager-analytics)
- Return snippets via API, CLI, MCP, and render in UI for copy/paste.

### 3.3 Tracking blueprints (presets)

**FR‑BP‑1: Preset categories**

Ship at least three built‑in tracking blueprints:

1. **SaaS / product site**
   - Events: `page_view`, `signup_started`, `signup_completed`, `cta_click`, `pricing_view`, `login`, `trial_started`.  
   - Parameters: `plan_name`, `source`, `campaign`, optional `user_role`.

2. **Ecommerce**
   - Events: `view_item`, `select_item`, `add_to_cart`, `begin_checkout`, `add_payment_info`, `purchase`, `refund`.  
   - Parameters: `item_id`, `item_name`, `item_category`, `value`, `currency`. [blog.bismart](https://blog.bismart.com/en/kale/google-analytics-4)

3. **Content / blog / publisher**
   - Events: `page_view`, `scroll_depth`, `article_read`, `video_play`, `newsletter_subscribe`.  
   - Parameters: `article_id`, `category`, `scroll_percent`, `engaged_time`.

**FR‑BP‑2: Blueprint config files**

- Store blueprints as structured config files (YAML/JSON) in the repo:
  - Define GA4 event names, parameters, recommended triggers, dataLayer keys.  
- Enable extension via custom blueprints (user‑defined configs in `plugins/blueprints`).

**FR‑BP‑3: Blueprint application**

- For a given site + blueprint:
  - Automatically create corresponding GA4 events (via recommended conventions where applicable).  
  - Create GTM tags/triggers that fire those events.  
  - Optionally generate a dataLayer helper snippet for the site.

### 3.4 Consent & privacy presets

**FR‑CONSENT‑1: Consent modes**

Presets:

- `none` – no consent gating (for dev/lab).  
- `basic` – simple boolean consent based on `dataLayer` or a cookie.  
- `advanced` – integrate with common CMPs (e.g., one or two well‑known consent manager patterns) via dataLayer events.

**FR‑CONSENT‑2: Consent‑aware GTM triggers**

- For `basic` and `advanced`:
  - GA4 tags fire only when consent is granted (e.g., `analytics_storage = 'granted'`).  
  - GTM triggers respect consent signals and filter events accordingly. [ituonline](https://www.ituonline.com/blogs/reviewing-top-ga4-tag-management-tools-which-one-fits-your-business/)

**FR‑CONSENT‑3: Documentation and transparency**

- In UI and `describe_analytics_setup` MCP tool, clearly explain:
  - What data is collected under each preset.  
  - What consent assumptions exist.

### 3.5 Cross‑domain and multi‑environment support

**FR‑CD‑1: Cross‑domain config**

- Allow per‑site config:
  - `primary_domain`, `linked_domains` (for cross‑domain tracking).  
- Automatically:
  - Configure GA4 cross‑domain measurement and GTM link decoration where possible. [ituonline](https://www.ituonline.com/blogs/reviewing-top-ga4-tag-management-tools-which-one-fits-your-business/)

**FR‑ENV‑1: Environments**

- Each site can have:
  - Separate GA4 properties per `environment` (dev, stage, prod).  
  - Separate GTM containers or distinct workspaces. [wherescape](https://www.wherescape.com/blog/data-automation/)
- UI and CLI show environment clearly; MCP tools accept `environment` parameter.

### 3.6 Governance, audit, and rollback

**FR‑GOV‑1: Audit log**

- Log every GA4 and GTM operation:
  - Operation type, user/agent, timestamp, old vs new IDs.  
- Store logs per site and allow viewing/filtering via UI and CLI. [ortech.com](https://ortech.com.my/insights/analytics-automation-platform/)

**FR‑GOV‑2: GTM config diff**

- For each published change:
  - Compute a diff between previous and current GTM configuration (tags, triggers, variables).  
- UI view: human‑friendly GTM diff for troubleshooting.

**FR‑GOV‑3: Config versioning & rollback**

- Version platform‑level configuration:
  - Per site blueprint config, GA4 mappings, GTM tag configuration.  
- Provide rollback:
  - `rollback --domain example.com --version <id>` to restore previous GTM config and GA4 mapping where feasible.

### 3.7 Health checks, monitoring, and alerts

**FR‑HEALTH‑1: Scheduled health checks**

- Periodic job per site:
  - Use GA4 Data API to check recent event volume, conversions, and funnels. [support.google](https://support.google.com/analytics/answer/9164320?hl=en)
  - Detect anomalies: zero events, drop beyond threshold, missing conversions.

**FR‑HEALTH‑2: Health dashboard**

- Web UI includes:
  - Status indicators per site:
    - Data flowing?  
    - Conversions firing?  
    - Last updated?  

**FR‑HEALTH‑3: Alerts & webhooks**

- Configurable thresholds:
  - Send alerts via email/Slack/webhooks when:
    - Page views drop to zero for 24+ hours.  
    - Key conversions drop sharply vs baseline.  
    - Measurement ID/GTM container mismatch is detected. [support.google](https://support.google.com/analytics/answer/9164320?hl=en)

### 3.8 Web UI

**FR‑UI‑1: Dashboard**

- Displays list of sites with:
  - Domain, name, environment.  
  - GA4 property ID, Measurement ID.  
  - GTM container ID, latest version.  
  - Health and consent preset status.

**FR‑UI‑2: Create analytics setup workflow**

- Form:
  - Site name, domain, environment.  
  - Blueprint preset (SaaS/ecommerce/content/custom).  
  - Consent preset.  
  - BigQuery export flag and dataset config.  
- On submit:
  - Calls backend; shows progress and result (IDs, snippets, blueprint summary).

**FR‑UI‑3: Blueprint editor**

- Simple interface to:
  - View existing blueprint config.  
  - Edit or create custom blueprints (advanced users).  
  - Apply blueprint to a site.

**FR‑UI‑4: Health & logs views**

- Health page:
  - Charts/time series of key KPIs from GA4 (visits, conversions).  
- Audit page:
  - List of operations with filters and details.  
  - GTM diff view.

### 3.9 CLI

**FR‑CLI‑1: Commands**

- `analytics-mcp create --domain example.com --name "Example Site" --env prod --blueprint saas --consent basic --enable-bigquery`
- `analytics-mcp status --domain example.com`
- `analytics-mcp apply-blueprint --domain example.com --blueprint ecommerce`
- `analytics-mcp health --domain example.com`
- `analytics-mcp rollback --domain example.com --version 3`
- `analytics-mcp list`

**FR‑CLI‑2: Output format**

- JSON output by default, human‑readable pretty print option.  
- Stable schema for CI/CD integration and agent usage.

### 3.10 REST API

**FR‑API‑1: Endpoints**

- `POST /sites`  
- `GET /sites/:domain`  
- `GET /sites`  
- `POST /sites/:domain/blueprint`  
- `GET /sites/:domain/health`  
- `POST /sites/:domain/rollback`  

**FR‑API‑2: Auth**

- Token‑based auth (API keys or OAuth2) for external callers.  
- Role support (read‑only vs admin) for access control.

### 3.11 MCP server and AI tools

Using MCP reference patterns and FastMCP. [developers.googleblog](https://developers.googleblog.com/gemini-cli-fastmcp-simplifying-mcp-server-development/)

**FR‑MCP‑1: Tools**

At minimum:

1. `create_analytics_setup`
   - Args: `domain`, `name`, `environment`, `blueprint`, `consent`, `enable_bigquery`.  
   - Returns: GA4/GTM IDs, snippets, blueprint summary.

2. `get_analytics_status`
   - Args: `domain`.  
   - Returns: GA4/GTM mapping, health status, consent preset.

3. `apply_tracking_blueprint`
   - Args: `domain`, `blueprint`.  
   - Returns: list of events/tags created/updated.

4. `describe_analytics_setup`
   - Args: `domain`.  
   - Returns: human‑readable explanation of what’s tracked, how consent works, what environment mappings exist.

5. `get_health_status`
   - Args: `domain`.  
   - Returns: recent metrics, anomaly flags.

**FR‑MCP‑2: Config examples for clients**

- Include:
  - Claude Desktop config example. [developer.microsoft](https://developer.microsoft.com/blog/claude-ready-secure-mcp-apim)
  - Claude Custom Integration remote MCP example.  
  - Gemini CLI FastMCP setup snippet. [youtube](https://www.youtube.com/watch?v=FE1LChbgFEw&vl=en)
  - Generic MCP client config example from resources. [github](https://github.com/cyanheads/model-context-protocol-resources)

### 3.12 Plugin system

**FR‑PLUG‑1: Blueprint plugins**

- Allow user‑contributed blueprints in a `plugins/blueprints` directory.  
- Load them at startup and expose them in UI, CLI, MCP tools.

**FR‑PLUG‑2: Integration plugins**

- Support plugins for:
  - Specific CMS/framework patterns (e.g. Next.js, WordPress, Craft).  
  - Specific consent managers or third‑party tools.

***

## 4. Non‑functional requirements

### 4.1 Security

- Secure storage of Google Cloud credentials (KMS/Secrets Manager).  
- Role‑based access to create/modify analytics setups.  
- MCP server protected behind appropriate auth for remote integrations. [developer.microsoft](https://developer.microsoft.com/blog/claude-ready-secure-mcp-apim)

### 4.2 Performance

- Initial setup (GA4 + GTM + blueprint application) should complete within 30 seconds under normal conditions.  
- Health checks should be efficient (batch GA4 Data API calls). [ortech.com](https://ortech.com.my/insights/analytics-automation-platform/)

### 4.3 Reliability

- Idempotent operations:
  - Re‑running `create_analytics_setup` for same domain should reuse existing property/container unless forced.  
- Clear error handling:
  - Errors from GA4/GTM APIs are surfaced with actionable messages.

### 4.4 Observability

- Centralized logging of:
  - API calls.  
  - MCP tool invocations.  
  - CLI usage.  
- Metrics on:
  - Number of sites, operations, failures.

***

## 5. Repository structure, DX, and documentation

### 5.1 Repo layout

```text
analytics-mcp/
  backend/
    src/
      services/      # GA4Service, GTMService, BlueprintService, HealthService
      api/           # REST controllers
      mcp/           # MCP server implementation
      plugins/       # optional integrations
    tests/
  cli/
    analytics_cli.py or index.ts
  web-ui/
    src/
      pages/
      components/
  config/
    env.example
    mcp-claude.example.json
    gemini-fastmcp.example.sh
  docs/
    blueprints/
    recipes/
  README.md
  LICENSE
  docker-compose.yml
```

### 5.2 README / docs

- Clear tagline and screenshots.  
- Quickstart:
  - Enable GA APIs, create service account, set credentials. [github](https://github.com/Bin-Huang/google-analytics-cli)
  - Run `docker-compose up`.  
  - Use UI and CLI to create first site.  
- Client integrations:
  - Claude / Gemini / generic MCP.  
- Recipes:
  - SaaS, ecommerce, content site setups.

***

## 6. Success metrics

- Time to analytics setup per new site < 1 minute (down from 20–30 minutes manually). [foodbloggerpro](https://www.foodbloggerpro.com/blog/ga4-property/)
- Number of GitHub stars and forks after release; aim to be listed on “Awesome MCP Servers” and “best analytics automation tools”. [snyk](https://snyk.io/articles/11-data-science-mcp-servers-for-sourcing-analyzing-and-visualizing-data/)
- Adoption: number of sites managed and blueprints applied via the platform.  
- Agent usage: number of MCP calls from Claude/Gemini clients, and inclusion in “best MCP servers for Claude Code” lists. [truefoundry](https://www.truefoundry.com/blog/best-mcp-servers-for-claude-code)



***

This PRD is intentionally full‑scope: GA4 + GTM automation, opinionated tracking, consent/privacy, cross‑domain, governance/rollback, health monitoring, BigQuery, UI/CLI/API/MCP, and plugin/extensibility. If you want, I can follow up with a high‑level architecture diagram and concrete class/module breakdown (e.g., `GA4Service`, `GTMService`, `BlueprintService`, `HealthService`) matching this PRD so you can go straight into design/implementation.