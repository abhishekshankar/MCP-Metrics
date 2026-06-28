# Content / Blog Site Setup Recipe

## Overview
Set up engagement tracking for a content site or blog.

## Steps

1. **Create setup**
   ```bash
   analytics-mcp create \
     --domain blog.example.com \
     --name "Example Blog" \
     --env prod \
     --blueprint content \
     --consent basic
   ```

2. **Add scroll depth tracking**:
   ```javascript
   trackContent('scroll_depth', { scroll_percent: 75, article_id: 'post-123' });
   trackContent('article_read', { article_id: 'post-123', category: 'tech', engaged_time: 120 });
   ```

3. **Use MCP from Claude Desktop** — add `config/mcp-claude.example.json` to your Claude config, then ask:
   > "Create analytics for blog.example.com using the content blueprint"

4. **Monitor via Web UI** at http://localhost:5173

## Events Tracked
- `page_view`, `scroll_depth`, `article_read`, `video_play`, `newsletter_subscribe`
