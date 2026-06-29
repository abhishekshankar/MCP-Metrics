# MCP-Metrics - Make commands for easy development

.PHONY: help demo install dev stop clean test lint

help: ## Show this help
	@echo "MCP-Metrics - Quick Commands"
	@echo "=============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

demo: ## One-command demo - starts everything with mock data
	@./demo.sh

install: ## Install Python dependencies
	pip install -e ".[dev]"
	@echo "✅ Dependencies installed"

dev: ## Start development server (requires: make install first)
	@echo "🚀 Starting development server..."
	@echo "   API: http://localhost:8000"
	@cd backend/src && PYTHONPATH=../../backend/src API_SECRET_KEY=dev ADMIN_API_KEY=dev READONLY_API_KEY=dev MOCK_GOOGLE_APIS=true uvicorn main:app --reload

web: ## Start web UI dev server (in new terminal)
	@echo "🌐 Starting Web UI..."
	@cd web-ui && npm install && npm run dev

stop: ## Stop all Docker services
	@docker-compose down
	@echo "🛑 Services stopped"

clean: ## Stop and remove all data (WARNING: deletes database!)
	@docker-compose down -v
	@echo "🧹 All services and data cleaned"

test: ## Run all tests
	@API_SECRET_KEY=test ADMIN_API_KEY=test READONLY_API_KEY=test python -m pytest backend/tests/ -q

lint: ## Run linter
	@ruff check backend/src/ backend/tests/ cli/

shell: ## Open shell in running API container
	@docker-compose exec api bash

logs: ## View API logs
	@docker-compose logs -f api

status: ## Check service status
	@echo "Service Status:"
	@docker-compose ps
	@echo ""
	@echo "Health Check:"
	@curl -s http://localhost:8000/health || echo "❌ API not responding"
