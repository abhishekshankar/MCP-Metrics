# Ecommerce Site Setup Recipe

## Overview
Set up GA4 recommended ecommerce events via GTM for an online store.

## Steps

1. **Create setup**
   ```bash
   analytics-mcp create \
     --domain shop.example.com \
     --name "Example Store" \
     --env prod \
     --blueprint ecommerce \
     --consent advanced
   ```

2. **Configure cross-domain** (if checkout is on a subdomain):
   ```bash
   analytics-mcp create \
     --domain shop.example.com \
     --name "Example Store" \
     --linked-domains checkout.example.com,shop.example.com
   ```

3. **Implement ecommerce dataLayer**:
   ```javascript
   trackEcommerce('purchase', [{ item_id: 'SKU123', item_name: 'Widget', price: 29.99 }], {
     value: 29.99,
     currency: 'USD'
   });
   ```

4. **Enable BigQuery export** (optional):
   ```bash
   analytics-mcp create \
     --domain shop.example.com \
     --name "Example Store" \
     --blueprint ecommerce \
     --enable-bigquery \
     --bigquery-project my-gcp-project \
     --bigquery-dataset analytics_export
   ```

## Events Tracked
- `view_item`, `select_item`, `add_to_cart`, `begin_checkout`, `add_payment_info`, `purchase`, `refund`
