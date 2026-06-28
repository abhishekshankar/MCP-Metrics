#!/bin/bash
# Gemini CLI FastMCP setup for Analytics MCP
# Usage: source config/gemini-fastmcp.example.sh

export DATABASE_URL="postgresql://analytics:analytics@localhost:5432/analytics_mcp"
export MOCK_GOOGLE_APIS="true"
export PYTHONPATH="backend/src"

# Run MCP server via FastMCP
python -m backend.src.mcp.server
