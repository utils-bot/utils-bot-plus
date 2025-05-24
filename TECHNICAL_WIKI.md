# UtilsBot+ - Technical Wiki

Comprehensive technical documentation for developers and advanced users.

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Systems](#core-systems)
- [Cogs (Command Modules)](#cogs-command-modules)
- [Database Schema](#database-schema)
- [Configuration](#configuration)
- [Security & Permissions](#security--permissions)
- [API Integrations](#api-integrations)
- [Development Guide](#development-guide)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## 🏗️ Architecture Overview

UtilsBot+ follows a modern, modular architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Discord API   │    │   Google AI     │    │  External APIs  │
│   (discord.py)  │    │   (Gemini)      │    │  (Screenshot)   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │      Bot Core             │
                    │   (core/bot.py)           │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │    Command Router         │
                    │  (Slash Commands Only)    │
                    └─────────────┬─────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                       │                       │
┌───────▼───────┐    ┌─────────▼────────┐    ┌─────────▼────────┐
│     Cogs       │    │    Database      │    │    Utilities     │
│  (Features)    │    │  (SQLAlchemy)    │    │  (Helpers)       │
└────────────────┘    └──────────────────┘    └──────────────────┘
```

### Key Design Principles

1. **Slash Commands Only** - No prefix commands for better UX
2. **Async First** - Full async/await architecture
3. **Type Safety** - Complete type hints and validation
4. **Modular Design** - Feature separation via cogs
5. **Error Resilience** - Comprehensive error handling
6. **Security First** - Permission-based access control

## 🔧 Core Systems

### Bot Core (`core/bot.py`)

The main bot class extends `commands.Bot` with custom functionality:

```python
class UtilsBot+(commands.Bot):
    def __init__(self):
        # Slash commands only setup
        super().__init__(
            command_prefix="$disabled$",  # Unused
            intents=discord.Intents.default(),
            help_command=None
        )
```

**Key Features:**
- Automatic cog loading from `cogs/` directory
- Database initialization and management
- Global error handling for slash commands
- Command syncing (global and guild-specific)
- Uptime and performance tracking

### Logging System (`core/logger.py`)

Structured logging with multiple output formats:

```python
# Console output (development)
structlog.dev.ConsoleRenderer(colors=True)

# JSON output (production)
structlog.processors.JSONRenderer()
```

**Features:**
- Rotating file logs (10MB max, 5 backups)
- Structured context with user/guild info
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Integration with external monitoring (Sentry support)

### Database Layer (`models/database.py`)

Modern SQLAlchemy 2.0 with async support:

```python
# Async session factory
self.async_session = async_sessionmaker(
    self.engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

**Supported Databases:**
- SQLite (default) - `sqlite+aiosqlite:///data/bot.db`
- PostgreSQL - `postgresql+asyncpg://user:pass@host/db`
- MySQL - `mysql+aiomysql://user:pass@host/db`

## 🎮 Cogs (Command Modules)

### AI Cog (`cogs/ai.py`)

**Google Gemini Integration**

Commands:
- `/ask` - Single question to Gemini
- `/chat` - Interactive conversation modal

**Technical Details:**
```python
# Uses Gemini 1.5 Flash (free tier)
self.model = genai.GenerativeModel('models/gemini-1.5-flash')

# Rate limiting: 3 questions per 60 seconds
@cooldown(rate=3, per=60)
```

**Features:**
- Async generation with `asyncio.to_thread()`
- Response truncation for Discord limits (3800 chars)
- Usage tracking in database
- Interactive chat with continue/end buttons

### Games Cog (`cogs/games.py`)

**Wordle Implementation**

Full Wordle game with:
- 5-letter word validation
- Color-coded feedback (🟩🟨⬛)
- 6 attempt limit
- Game state management
- Statistics tracking

**Technical Implementation:**
```python
class WordleGame:
    def format_guess(self, guess: str) -> str:
        # Two-pass algorithm for accurate coloring
        # 1. Mark exact matches (green)
        # 2. Mark wrong positions (yellow)
        # 3. Mark incorrect letters (black)
```

**Data Source:**
- Word list: `assets/games/wordle_words.txt`
- Fallback to hardcoded words if file missing

### Network Cog (`cogs/network.py`)

**Screenshot Service**
```python
class ScreenshotService:
    async def capture_screenshot(
        self, url, width=1920, height=1080,
        full_page=False, wait_time=2
    ) -> Optional[bytes]
```

**Commands:**
- `/screenshot` - Website screenshots via external API
- `/ip` - IP geolocation via ip-api.com
- `/unshorten` - URL expansion with redirect following

**Security Features:**
- URL validation and sanitization
- Private IP detection
- Suspicious domain warnings
- Request timeouts and rate limiting

### Tools Cog (`cogs/tools.py`)

**Security Tools:**
- `/totp` - Time-based OTP generation (pyotp)
- `/password` - Cryptographically secure passwords

**Utility Tools:**
- `/qr` - QR code generation (configurable sizes)
- `/base64` - Encoding/decoding
- `/hash` - MD5, SHA1, SHA256, SHA512

**Implementation Example:**
```python
# TOTP with proper validation
totp = pyotp.TOTP(cleaned_secret)
current_code = totp.now()
time_remaining = 30 - (int(time.time()) % 30)
```

### Info Cog (`cogs/info.py`)

**Bot Information:**
- System stats (CPU, memory, uptime)
- Discord stats (guilds, users, commands)
- Performance metrics (latency, response times)

**Whitelist Management:**
- `/whitelist add/remove/list/check` (dev-only)
- Database-backed user permissions
- Beta feature access control

### System Cog (`cogs/system.py`)

**Developer Commands:**
- `/sync` - Command synchronization (global/guild)
- `/eval` - Python code execution with safety
- `/reload/load/unload` - Dynamic cog management

**Safety Features:**
```python
# Secure eval environment
env = {
    'bot': self.bot,
    'interaction': interaction,
    'discord': discord,
    # Limited scope for safety
}
```

## 🗄️ Database Schema

### Tables

**Users Table:**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    discord_id VARCHAR(20) UNIQUE,
    username VARCHAR(100),
    is_whitelisted BOOLEAN DEFAULT FALSE,
    is_blacklisted BOOLEAN DEFAULT FALSE,
    created_at DATETIME,
    updated_at DATETIME
);
```

**Guilds Table:**
```sql
CREATE TABLE guilds (
    id INTEGER PRIMARY KEY,
    discord_id VARCHAR(20) UNIQUE,
    name VARCHAR(100),
    prefix VARCHAR(10) DEFAULT '!',
    is_blacklisted BOOLEAN DEFAULT FALSE,
    created_at DATETIME,
    updated_at DATETIME
);
```

**Game Stats Table:**
```sql
CREATE TABLE game_stats (
    id INTEGER PRIMARY KEY,
    user_discord_id VARCHAR(20),
    game_type VARCHAR(50),  -- 'wordle', etc.
    games_played INTEGER DEFAULT 0,
    games_won INTEGER DEFAULT 0,
    best_score INTEGER DEFAULT 0,
    created_at DATETIME,
    updated_at DATETIME
);
```

**API Usage Table:**
```sql
CREATE TABLE api_usage (
    id INTEGER PRIMARY KEY,
    user_discord_id VARCHAR(20),
    api_name VARCHAR(50),  -- 'gemini', 'screenshot', etc.
    usage_count INTEGER DEFAULT 0,
    last_used DATETIME,
    created_at DATETIME
);
```

## ⚙️ Configuration

### Environment Variables

**Required:**
```env
BOT_TOKEN=discord_bot_token
DEV_IDS=123456789,987654321  # Comma-separated
GEMINI_API_KEY=gemini_api_key
SECRET_KEY=encryption_key
```

**Optional Features:**
```env
# Feature toggles
ENABLE_GAMES=true
ENABLE_NETWORK_TOOLS=true
ENABLE_AI_COMMANDS=true
ENABLE_SYSTEM_COMMANDS=true

# External APIs
SCREENSHOT_API_KEY=screenshot_service_key
RAPIDAPI_KEY=rapid_api_key

# Monitoring
SENTRY_DSN=sentry_error_tracking_url
ENABLE_METRICS=false

# Caching
REDIS_URL=redis://localhost:6379
CACHE_TTL=300
```

**Rate Limiting:**
```env
GLOBAL_RATE_LIMIT=5  # Commands per minute per user
COOLDOWN_RATE=2      # Seconds between commands
```

### Settings Validation

Pydantic-based configuration with validation:

```python
class Settings(BaseModel):
    bot_token: str
    dev_ids: List[int] = []
    gemini_api_key: str
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
```

## 🔒 Security & Permissions

### Access Control Layers

1. **Developer Check** - `@dev_only()`
2. **Whitelist Check** - `@requires_whitelist()`
3. **Guild Check** - `@guild_only()`
4. **Cooldown** - `@cooldown(rate, per)`

### Permission Decorators

```python
def requires_whitelist() -> Callable:
    async def predicate(interaction: discord.Interaction) -> bool:
        if not settings.closed_beta:
            return True  # Open access
        
        if is_developer(interaction.user.id):
            return True  # Developers bypass
        
        # Check database whitelist
        user = await bot.db.get_user(interaction.user.id)
        return user and user.is_whitelisted
    
    return discord.app_commands.check(predicate)
```

### Security Features

- **Input Validation** - All user inputs sanitized
- **Rate Limiting** - Per-user command cooldowns
- **URL Validation** - Prevents private IP access
- **Secret Handling** - Environment-based configuration
- **Error Hiding** - Stack traces only in logs

## 🔌 API Integrations

### Google Gemini AI

**Setup:**
```python
import google.generativeai as genai
genai.configure(api_key=settings.gemini_api_key)
model = genai.GenerativeModel('models/gemini-1.5-flash')
```

**Usage Patterns:**
- Free tier: 15 requests per minute
- Input limit: ~1M tokens
- Output limit: 8,192 tokens
- Async execution to prevent blocking

### Screenshot Services

**Primary: ScreenshotOne API**
```python
params = {
    'url': url,
    'viewport_width': 1920,
    'viewport_height': 1080,
    'format': 'png',
    'full_page': full_page,
    'block_ads': True,
    'cache': True
}
```

**Fallback: Basic HTTP + Placeholder**
- Generates simple placeholder image
- Can be extended with Playwright/Selenium

### IP Geolocation

**Service: ip-api.com (Free)**
```python
url = f"http://ip-api.com/json/{ip}"
# Returns: country, region, city, ISP, coordinates
```

**Features:**
- No API key required
- 1000 requests/month free
- Comprehensive location data

## 🛠️ Development Guide

### Project Structure

```
utils-bot-plus/
├── main.py                 # Entry point
├── config/
│   ├── __init__.py
│   └── settings.py         # Pydantic configuration
├── core/
│   ├── __init__.py
│   ├── bot.py             # Main bot class
│   └── logger.py          # Structured logging
├── cogs/                  # Command modules
│   ├── ai.py             # Gemini integration
│   ├── games.py          # Interactive games
│   ├── info.py           # Bot information
│   ├── network.py        # Network utilities
│   ├── system.py         # Developer tools
│   └── tools.py          # Utility commands
├── models/
│   ├── __init__.py
│   └── database.py       # SQLAlchemy models
├── utils/
│   ├── __init__.py
│   ├── checks.py         # Permission decorators
│   ├── embeds.py         # Discord embed helpers
│   ├── health.py         # Monitoring utilities
│   └── screenshot.py     # Screenshot service
├── assets/
│   └── games/
│       └── wordle_words.txt
├── migrations/           # Database setup
│   ├── init_db.py
│   └── populate_data.py
├── data/                 # SQLite database
├── logs/                 # Log files
└── requirements.txt
```

### Adding New Commands

1. **Create Command in Cog:**
```python
@app_commands.command(name="newcommand", description="Description")
@app_commands.describe(param="Parameter description")
@requires_whitelist()  # Add appropriate checks
@cooldown(rate=5, per=60)  # Set rate limits
async def new_command(self, interaction: discord.Interaction, param: str):
    # Implementation
    pass
```

2. **Add Error Handling:**
```python
try:
    # Command logic
    embed = create_success_embed("Success", "Operation completed")
    await interaction.response.send_message(embed=embed)
except Exception as e:
    self.logger.error(f"Command error: {e}")
    embed = create_error_embed("Error", "Operation failed")
    await interaction.response.send_message(embed=embed, ephemeral=True)
```

3. **Update Documentation:**
- Add to this wiki
- Update README command list
- Add usage examples

### Testing Commands

```bash
# Run bot in development mode
make run-dev

# Enable debug logging
echo "DEBUG=true" >> .env

# Sync commands to test guild
# Use /sync command in Discord

# Check logs
tail -f logs/bot.log
```

### Code Style

**Formatting:**
```bash
# Auto-format code
make format

# Check formatting
make format-check
```

**Type Hints:**
```python
from typing import Optional, List, Dict, Any

async def example_function(
    interaction: discord.Interaction,
    text: str,
    optional_param: Optional[int] = None
) -> Dict[str, Any]:
    """Function with proper type hints and docstring."""
    return {"result": "success"}
```

## 🚀 Deployment

### Local Development

```bash
# Setup development environment
git clone <repository>
cd utils-bot-plus
make dev

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run with hot reload
make run-dev
```

### Production Deployment

**Docker (Recommended):**
```bash
# Build image
docker build -t utils-bot-plus .

# Run with compose
docker-compose up -d

# Check logs
docker-compose logs -f bot
```

**Traditional VPS:**
```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup systemd service
sudo cp utils-bot.service /etc/systemd/system/
sudo systemctl enable utils-bot
sudo systemctl start utils-bot
```

**Environment Variables:**
```bash
# Production settings
DEBUG=false
LOG_LEVEL=INFO
AUTO_SYNC_COMMANDS=true

# Enable monitoring
SENTRY_DSN=your_sentry_url
ENABLE_METRICS=true

# Use PostgreSQL in production
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/utils_bot
```

### Health Monitoring

```python
# Health check endpoint (if implemented)
GET /health
{
    "status": "healthy",
    "uptime": "2d 3h 45m",
    "guild_count": 150,
    "latency_ms": 45,
    "checks": {
        "database": true,
        "discord_api": true,
        "external_apis": {
            "gemini": true,
            "redis": false
        }
    }
}
```

## 🐛 Troubleshooting

### Common Issues

**Bot Won't Start:**
```bash
# Check Python version
python3 --version  # Should be 3.11+

# Verify dependencies
pip install -r requirements.txt

# Check environment variables
cat .env | grep -E "(BOT_TOKEN|GEMINI_API_KEY)"

# Check permissions
ls -la data/ logs/
```

**Commands Not Syncing:**
```bash
# Manual sync (developer only)
# Use /sync command in Discord

# Check command tree
# Use /eval len(bot.tree.get_commands())

# Reset command cache
# Restart bot or use /reload system
```

**Database Errors:**
```bash
# Reset database
rm data/bot.db
python migrations/init_db.py

# Check database file permissions
ls -la data/

# Test database connection
python -c "
from models.database import Database
import asyncio
async def test():
    db = Database('sqlite+aiosqlite:///data/bot.db')
    await db.initialize()
    print('Database OK')
asyncio.run(test())
"
```

**Permission Errors:**
- Ensure bot has `applications.commands` scope
- Check server permissions for bot role
- Verify user is whitelisted (if beta mode enabled)
- Check developer IDs in DEV_IDS environment variable

**API Failures:**
```bash
# Test Gemini API
python -c "
import google.generativeai as genai
genai.configure(api_key='your_key')
model = genai.GenerativeModel('models/gemini-1.5-flash')
response = model.generate_content('Hello')
print(response.text)
"

# Check screenshot service
curl -X GET "https://api.screenshotone.com/take?url=https://example.com" \
     -H "Authorization: Bearer your_api_key"
```

### Debug Mode

Enable comprehensive debugging:

```env
# .env
DEBUG=true
LOG_LEVEL=DEBUG
```

**Debug Output:**
- SQL queries logged
- API request/response details
- Command execution timing
- User permission checks
- Error stack traces

### Log Analysis

```bash
# Filter error logs
grep "ERROR" logs/bot.log

# Monitor real-time
tail -f logs/bot.log | grep -E "(ERROR|WARNING)"

# Command usage stats
grep "app_commands" logs/bot.log | wc -l

# Find specific user activity
grep "user_id:123456789" logs/bot.log
```

### Performance Monitoring

**Memory Usage:**
```python
# Add to bot stats
import psutil
process = psutil.Process()
memory_mb = process.memory_info().rss / 1024 / 1024
```

**Database Performance:**
```sql
-- SQLite query analysis
EXPLAIN QUERY PLAN SELECT * FROM users WHERE discord_id = ?;

-- Add indexes for performance
CREATE INDEX idx_users_discord_id ON users(discord_id);
CREATE INDEX idx_api_usage_user_api ON api_usage(user_discord_id, api_name);
```

**Command Response Times:**
```python
# Add timing to commands
import time

start_time = time.time()
# Command logic here
response_time = (time.time() - start_time) * 1000
logger.info(f"Command completed in {response_time:.2f}ms")
```

---

This technical wiki provides complete documentation for understanding, developing, and maintaining UtilsBot+. For basic usage, see the [Simple README](README_SIMPLE.md).
