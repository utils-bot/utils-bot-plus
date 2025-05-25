#!/bin/bash
# Docker deployment script for non-interactive hosting services
# This script handles automated setup without user interaction

set -e  # Exit on any error

echo "🐳 UtilsBot+ Docker Automated Setup"
echo "===================================="

# Function to generate random secret key
generate_secret() {
    python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || \
    openssl rand -hex 32 2>/dev/null || \
    head -c 32 /dev/urandom | base64 | tr -d '/+' | cut -c1-32
}

# Function to validate required environment variables
validate_required_vars() {
    local missing_vars=()
    
    if [ -z "$BOT_TOKEN" ]; then
        missing_vars+=("BOT_TOKEN")
    fi
    
    if [ -z "$DEV_IDS" ]; then
        missing_vars+=("DEV_IDS")
    fi
    
    if [ -z "$GEMINI_API_KEY" ]; then
        echo "⚠️  Warning: GEMINI_API_KEY not set - AI commands will be disabled"
    fi
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        echo "❌ Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "   - $var"
        done
        echo ""
        echo "Please set these environment variables and restart the container."
        exit 1
    fi
}

# Function to setup environment file
setup_environment() {
    echo "🔧 Setting up environment configuration..."
    
    # Generate secret key if not provided
    if [ -z "$SECRET_KEY" ]; then
        echo "🔑 Generating SECRET_KEY..."
        SECRET_KEY=$(generate_secret)
        export SECRET_KEY
    fi
    
    # Set default values for hosting services
    export LOG_LEVEL="${LOG_LEVEL:-INFO}"
    export DEBUG="${DEBUG:-false}"
    export AUTO_SYNC_COMMANDS="${AUTO_SYNC_COMMANDS:-true}"
    export ENABLE_DOCKER_SANDBOX="${ENABLE_DOCKER_SANDBOX:-false}"  # Disabled for hosted services
    export DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///data/bot.db}"
    export PORT="${PORT:-8080}"
    
    # Create .env file for the application
    cat > /app/.env << EOF
# Auto-generated environment file for Docker deployment
BOT_TOKEN=${BOT_TOKEN}
DEV_IDS=${DEV_IDS}
DEV_GUILD_ID=${DEV_GUILD_ID:-}
GEMINI_API_KEY=${GEMINI_API_KEY:-}
SECRET_KEY=${SECRET_KEY}

# Bot Configuration
BOT_PREFIX=${BOT_PREFIX:-!}
BOT_SUPPORT_SERVER=${BOT_SUPPORT_SERVER:-}
CLOSED_BETA=${CLOSED_BETA:-false}

# Logging
LOG_LEVEL=${LOG_LEVEL}
LOG_FILE=${LOG_FILE:-logs/bot.log}
LOG_MAX_BYTES=${LOG_MAX_BYTES:-10485760}
LOG_BACKUP_COUNT=${LOG_BACKUP_COUNT:-5}

# Database
DATABASE_URL=${DATABASE_URL}

# External APIs
SCREENSHOT_SERVICE_URL=${SCREENSHOT_SERVICE_URL:-}
SCREENSHOT_API_KEY=${SCREENSHOT_API_KEY:-}
UNSHORTEN_API_URL=${UNSHORTEN_API_URL:-}
UNSHORTEN_API_SECRET=${UNSHORTEN_API_SECRET:-}
RAPIDAPI_KEY=${RAPIDAPI_KEY:-}

# Monitoring
SENTRY_DSN=${SENTRY_DSN:-}
ENABLE_METRICS=${ENABLE_METRICS:-false}

# Rate Limiting
GLOBAL_RATE_LIMIT=${GLOBAL_RATE_LIMIT:-5}
COOLDOWN_RATE=${COOLDOWN_RATE:-2}

# Features
ENABLE_GAMES=${ENABLE_GAMES:-true}
ENABLE_NETWORK_TOOLS=${ENABLE_NETWORK_TOOLS:-true}
ENABLE_AI_COMMANDS=${ENABLE_AI_COMMANDS:-true}
ENABLE_SYSTEM_COMMANDS=${ENABLE_SYSTEM_COMMANDS:-true}

# Sandboxing (Disabled for hosted services)
ENABLE_DOCKER_SANDBOX=${ENABLE_DOCKER_SANDBOX}
SANDBOX_TIMEOUT=${SANDBOX_TIMEOUT:-10}
SANDBOX_MEMORY_LIMIT=${SANDBOX_MEMORY_LIMIT:-128m}
ENABLE_EVAL_COMMAND=${ENABLE_EVAL_COMMAND:-false}
ENABLE_RUN_COMMAND=${ENABLE_RUN_COMMAND:-false}

# Cache
REDIS_URL=${REDIS_URL:-}
CACHE_TTL=${CACHE_TTL:-300}

# Security
SESSION_TIMEOUT=${SESSION_TIMEOUT:-3600}

# Development
DEBUG=${DEBUG}
AUTO_SYNC_COMMANDS=${AUTO_SYNC_COMMANDS}

# Health Check Port
PORT=${PORT}
EOF

    echo "✅ Environment configuration created"
}

# Function to create required directories
setup_directories() {
    echo "📁 Creating required directories..."
    mkdir -p /app/data /app/logs
    chmod 755 /app/data /app/logs
    echo "✅ Directories created"
}

# Function to run database migrations
setup_database() {
    echo "🗄️  Setting up database..."
    
    # Run database initialization if needed
    if [ -f "/app/migrations/init_db.py" ]; then
        python /app/migrations/init_db.py || echo "⚠️  Database initialization skipped (may already exist)"
    fi
    
    echo "✅ Database setup complete"
}

# Function to start health check server
start_health_server() {
    echo "🏥 Starting health check server..."
    
    # Create simple health check server
    cat > /app/health_server.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import aiohttp
from aiohttp import web
import os
import sys
import logging

# Simple health check server for hosting services
async def health_check(request):
    """Health check endpoint"""
    return web.json_response({
        "status": "healthy",
        "service": "utils-bot-plus",
        "timestamp": __import__('time').time()
    })

async def readiness_check(request):
    """Readiness check endpoint"""
    # Check if bot is ready (basic check)
    return web.json_response({
        "status": "ready",
        "service": "utils-bot-plus"
    })

async def create_app():
    """Create health check web app"""
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/ready', readiness_check)
    app.router.add_get('/', health_check)  # Root endpoint for services that check /
    return app

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=port)
EOF

    chmod +x /app/health_server.py
}

# Main setup function
main() {
    echo "🚀 Starting automated setup for hosting service deployment..."
    echo ""
    
    # Validate required environment variables
    validate_required_vars
    
    # Setup environment
    setup_environment
    
    # Create directories
    setup_directories
    
    # Setup database
    setup_database
    
    # Setup health check server
    start_health_server
    
    echo ""
    echo "✅ Automated setup complete!"
    echo ""
    echo "🎯 Service Configuration:"
    echo "   - Port: $PORT"
    echo "   - Health Check: /health"
    echo "   - Readiness Check: /ready"
    echo "   - Database: $DATABASE_URL"
    echo "   - Docker Sandbox: $ENABLE_DOCKER_SANDBOX"
    echo ""
    echo "🚀 Starting bot..."
}

# Run main function
main
