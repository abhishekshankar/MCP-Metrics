# SaaS Site Setup Recipe

## Overview
Set up analytics for a SaaS product site with signup, pricing, and trial tracking.

## Steps

1. **Start the platform**
   ```bash
   docker compose up -d
   ```

2. **Create analytics setup**
   ```bash
   analytics-mcp create \
     --domain app.example.com \
     --name "Example SaaS" \
     --env prod \
     --blueprint saas \
     --consent basic
   ```

3. **Add GTM snippets** to your site `<head>` and `<body>` (returned in CLI output).

4. **Implement dataLayer events** using the helper snippet:
   ```javascript
   trackEvent('signup_started', { source: 'homepage', campaign: 'launch' });
   trackEvent('trial_started', { plan_name: 'pro', source: 'pricing' });
   ```

5. **Verify health**
   ```bash
   analytics-mcp health --domain app.example.com
   ```

## Events Tracked
- `signup_started`, `signup_completed`, `cta_click`, `pricing_view`, `login`, `trial_started`
