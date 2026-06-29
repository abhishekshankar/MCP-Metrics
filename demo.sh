#!/bin/bash
# One-command demo for MCP-Metrics
# Usage: ./demo.sh

set -e

echo "🚀 MCP-Metrics Quick Demo"
echo "========================"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker found"
echo ""

# Create .env if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file with demo settings..."
    cat > .env << 'EOF'
# Demo Configuration - Auto-generated
# These are DEVELOPMENT values - change for production!

API_SECRET_KEY=demo-secret-key-not-for-production
ADMIN_API_KEY=demo-admin-key-not-for-production
READONLY_API_KEY=demo-readonly-key-not-for-production
MOCK_GOOGLE_APIS=true
DATABASE_URL=postgresql+psycopg2://analytics:analytics@localhost:5433/analytics_mcp
GTM_ACCOUNT_ID=1234567
EOF
    echo "✅ .env created"
else
    echo "✅ .env already exists (using existing)"
fi
echo ""

# Start services
echo "🐳 Starting services with Docker Compose..."
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Check health
echo ""
echo "🔍 Checking service health..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API is ready!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Waiting... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "⚠️  API might not be ready yet, but continuing..."
fi

echo ""
echo "========================"
echo "🎉 Demo is running!"
echo "========================"
echo ""
echo "📊 Web UI:     http://localhost:5173"
echo "🔌 API:        http://localhost:8000"
echo "📚 API Docs:   http://localhost:8000/docs"
echo ""
echo "🧪 Try these:"
echo ""
echo "   1. Open http://localhost:5173"
echo "   2. Click 'Create Setup'"
echo "   3. Enter: test-site.com"
echo "   4. See fake GA4 property created instantly!"
echo ""
echo "   Or run CLI:"
echo "      docker-compose exec api python -m cli.analytics_cli create --domain demo.com"
echo ""
echo "🛑 To stop:    docker-compose down"
echo "🧹 To clean:   docker-compose down -v"
echo ""
echo "💡 This runs in MOCK mode - no Google credentials needed!"
echo "   All GA4/GTM responses are simulated for demo purposes."
echo ""

# Try to open browser (macOS/Linux)
if command -v open &> /dev/null; then
    echo "🌎 Opening browser..."
    sleep 2 && open http://localhost:5173 &
elif command -v xdg-open &> /dev/null; then
    echo "🌎 Opening browser..."
    sleep 2 && xdg-open http://localhost:5173 &
fi
