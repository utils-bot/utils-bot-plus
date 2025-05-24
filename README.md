# UtilsBot+

A modern, feature-rich Discord bot built with Python 3.11+ and discord.py 2.4+. Provides comprehensive utilities including AI integration, interactive games, network tools, security features, and developer commands—all through intuitive slash commands.

## Overview

UtilsBot+ is designed with a **slash commands-only** approach for the best user experience. Built on modern async architecture with comprehensive error handling, database integration, and modular design for easy maintenance and feature expansion.

### Key Highlights
- **Modern Architecture**: Async-first with type safety and comprehensive error handling
- **Slash Commands Only**: No prefix commands for cleaner Discord UX
- **AI-Powered**: Google Gemini integration with interactive chat capabilities
- **Security-First**: Permission layers, input validation, and user whitelisting
- **Production-Ready**: Structured logging, health monitoring, and database support
- **Developer-Friendly**: Hot reload, code evaluation, and dynamic cog management

## Complete Feature Overview

### AI Integration (`/ask`, `/chat`)
**Powered by Google Gemini 1.5 Flash (Free Tier)**
- **`/ask <question>`** - Quick AI responses with context awareness
- **`/chat`** - Interactive conversation modal with continue/end controls
- **Smart Features**: Response truncation, usage tracking, rate limiting (3 questions/minute)
- **Free Tier**: 15 requests per minute, up to 1M input tokens

### Interactive Games (`/wordle`)
**Full Wordle Implementation**
- **`/wordle`** - Start a new Wordle game with proper game mechanics
- **Game Features**: 
  - 6 attempts with color-coded feedback (🟩 correct position, 🟨 wrong position, ⬛ not in word)
  - Interactive UI with guess input modals and game controls
  - Statistics tracking (games played, won, best scores)
  - Active game management (one game per user)
- **Word Database**: 2000+ valid 5-letter words with fallback lists

### Network & Web Tools
**Screenshot Capture (`/screenshot`)**
- **`/screenshot <url>`** - High-quality website screenshots
- **Options**: Full page capture, custom viewport sizes, ad blocking
- **Security**: URL validation, private IP protection, timeout controls
- **Integration**: ScreenshotOne API with local fallback

**IP Information (`/ip`)**
- **`/ip <address>`** - Comprehensive IP geolocation lookup
- **Data Provided**: Country, region, city, ISP, coordinates, timezone
- **Features**: Country flag display, private IP detection, rate limiting
- **Source**: ip-api.com (1000 free requests/month)

**URL Management (`/unshorten`)**
- **`/unshorten <url>`** - Expand shortened URLs safely
- **Security Features**: Suspicious domain detection, redirect limits, safety warnings
- **Supported**: All major URL shorteners (bit.ly, tinyurl, etc.)

### Security & Utility Tools
**Two-Factor Authentication (`/totp`)**
- **`/totp <secret>`** - Generate TOTP codes for 2FA apps
- **Features**: Time remaining display, base32 validation, secure handling
- **Privacy**: Ephemeral responses, no secret storage

**QR Code Generation (`/qr`)**
- **`/qr <text>`** - Create QR codes with customizable sizes
- **Options**: Small, medium, large sizes with optimized parameters
- **Limits**: 2000 character input, PNG output format

**Text Utilities**
- **`/base64 <text> <encode|decode>`** - Base64 encoding/decoding
- **`/hash <text> <algorithm>`** - Generate MD5, SHA1, SHA256, SHA512 hashes
- **`/password`** - Generate cryptographically secure passwords

### Information & Help System
**Bot Information (`/info`, `/ping`, `/version`)**
- **`/info`** - Comprehensive bot statistics and system information
  - Server count, user count, uptime, memory usage, CPU usage
  - Feature toggles, performance metrics, technical details
- **`/ping`** - Latency testing with response time and WebSocket latency
- **`/version`** - Version information and changelog

**Dynamic Help System (`/help`)**
- **`/help`** - Interactive help with category filtering
- **Features**: Autocomplete categories, command descriptions, usage examples
- **Categories**: Information, AI, Games, Tools, Network, System

### User Management & Security
**Beta Whitelist System (`/whitelist`)**
- **`/whitelist add <user>`** - Add users to beta access (dev-only)
- **`/whitelist remove <user>`** - Remove beta access (dev-only)
- **`/whitelist list`** - View all whitelisted users (dev-only)
- **`/whitelist check <user>`** - Check whitelist status (dev-only)
- **Features**: Database-backed, automatic permission checks, closed beta support

### Developer & System Commands
**Command Management (`/sync`, `/reload`, `/load`, `/unload`)**
- **`/sync`** - Synchronize slash commands (global/guild/specific)
- **`/reload <cog>`** - Hot reload cogs without restart
- **`/load <cog>`** - Load new cogs dynamically
- **`/unload <cog>`** - Unload cogs (with safety checks)

**Code Execution (`/eval`)**
- **`/eval <code>`** - Execute Python code with secure environment
- **Safety**: Limited scope, output capture, error handling
- **Context**: Access to bot, interaction, Discord objects

**Bot Analytics (`/guilds`)**
- **`/guilds`** - List all servers with member counts (dev-only)
- **Features**: Paginated display, server statistics

## Quick Start Guide

### Prerequisites
- **Python 3.11+** (Python 3.12 recommended)
- **Discord Bot Token** ([Create here](https://discord.com/developers/applications))
- **Google Gemini API Key** ([Free tier here](https://aistudio.google.com/app/apikey))

### 1. Installation & Setup

```bash
# Clone the repository
git clone <your-repository-url>
cd utils-bot-plus

# Run automated setup (creates .env, directories, generates secrets)
chmod +x setup.sh
./setup.sh

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Edit `.env` file with your credentials:

```env
# REQUIRED SETTINGS
BOT_TOKEN=your_discord_bot_token_here
DEV_IDS=123456789012345678,987654321098765432  # Your Discord ID
DEV_GUILD_ID=1234567890123456789  # Your test server ID
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=auto_generated_32_char_hex_key

# OPTIONAL FEATURES (all enabled by default)
ENABLE_GAMES=true
ENABLE_NETWORK_TOOLS=true
ENABLE_AI_COMMANDS=true
ENABLE_SYSTEM_COMMANDS=true

# BETA ACCESS (set to false for public access)
CLOSED_BETA=false

# EXTERNAL APIS (optional)
SCREENSHOT_API_KEY=your_screenshot_api_key  # For enhanced screenshots
RAPIDAPI_KEY=your_rapidapi_key  # For additional APIs

# MONITORING (optional)
SENTRY_DSN=your_sentry_url  # Error tracking
ENABLE_METRICS=false  # Prometheus metrics
```

### 3. Database Setup & Launch

```bash
# Initialize database (creates SQLite by default)
python migrations/init_db.py

# Start the bot
python main.py
```

### 4. Discord Setup

1. **Invite Bot**: Use OAuth2 URL with `applications.commands` scope
2. **Test Commands**: Use `/info` to verify bot is working
3. **Sync Commands**: Use `/sync` to ensure all commands are available
4. **Set Permissions**: Ensure bot has necessary permissions in your server

## Troubleshooting

### Bot Won't Start
1. Check your `.env` file has all required values
2. Verify your bot token is correct
3. Ensure Python 3.11+ is installed
4. Check logs in `logs/bot.log` for detailed error information

### Commands Not Working
1. Run `/sync` command to sync slash commands
2. Check bot has proper permissions in your server
3. Verify you're whitelisted (if beta mode is enabled)

### Permission Errors
- Ensure bot has `Send Messages`, `Use Slash Commands` permissions
- For screenshots: needs `Attach Files` permission
- For embeds: needs `Embed Links` permission

### Debug Mode
Enable debug mode by setting `DEBUG=true` in your `.env` file for more verbose logging.

## Command Reference

### Available Commands by Category

| Category | Commands | Description |
|----------|----------|-------------|
| **AI** | `/ask`, `/chat` | Google Gemini AI integration |
| **Games** | `/wordle` | Interactive word games |
| **Network** | `/screenshot`, `/ip`, `/unshorten` | Web and network utilities |
| **Security** | `/totp`, `/qr`, `/base64`, `/hash`, `/password` | Security and encoding tools |
| **Info** | `/info`, `/ping`, `/version`, `/help` | Bot information and help |
| **Admin** | `/whitelist add/remove/list/check` | User management (dev-only) |
| **System** | `/sync`, `/eval`, `/reload`, `/load`, `/unload` | Developer tools (dev-only) |

### Command Details & Usage

```bash
# AI Commands
/ask question:"What is machine learning?" ephemeral:true
/chat  # Opens interactive modal

# Games
/wordle  # Starts new Wordle game

# Network Tools
/screenshot url:"https://example.com" full_page:true
/ip address:"8.8.8.8"
/unshorten url:"https://bit.ly/example"

# Security Tools
/totp secret:"YOUR2FASECRET" ephemeral:true
/qr text:"Hello World" size:"medium"
/base64 text:"Hello" operation:"encode"
/hash text:"password" algorithm:"sha256"

# Information
/info  # Comprehensive bot stats
/help category:"AI"  # Filtered help
/ping  # Latency test

# Admin Commands (Developer Only)
/whitelist add user:@username
/sync scope:"global"
/eval code:"print('Hello World')"
```

## Technical Architecture

### Core Technologies
- **Discord.py 2.4+**: Modern Discord API wrapper with slash command support
- **SQLAlchemy 2.0**: Async ORM with SQLite/PostgreSQL/MySQL support
- **Google Generative AI**: Gemini 1.5 Flash integration
- **Pydantic 2.8+**: Configuration validation and data modeling
- **Structlog**: Structured logging with JSON output
- **aiohttp/httpx**: Async HTTP clients for external APIs

### Project Structure
```
utils-bot-plus/
├── main.py                 # Application entry point
├── pyproject.toml         # Modern Python packaging
├── requirements.txt       # Production dependencies
├── .env.example          # Configuration template
│
├── config/               # Configuration management
│   ├── settings.py      # Pydantic settings with validation
│   └── __init__.py
│
├── core/                 # Core bot functionality
│   ├── bot.py           # Main UtilsBot+ class
│   ├── logger.py        # Structured logging setup
│   └── __init__.py
│
├── cogs/                 # Feature modules (slash commands)
│   ├── ai.py            # Google Gemini integration
│   ├── games.py         # Interactive games (Wordle)
│   ├── info.py          # Bot info & help system
│   ├── network.py       # Network utilities
│   ├── system.py        # Developer commands
│   └── tools.py         # Security & utility tools
│
├── models/               # Data models & database
│   ├── database.py      # SQLAlchemy models & management
│   └── __init__.py
│
├── utils/                # Utility functions
│   ├── checks.py        # Permission decorators
│   ├── embeds.py        # Discord embed helpers
│   ├── health.py        # Health monitoring
│   ├── screenshot.py    # Screenshot service
│   └── __init__.py
│
├── assets/               # Static resources
│   └── games/
│       └── wordle_words.txt  # Game word lists
│
├── migrations/           # Database setup scripts
│   ├── init_db.py       # Database initialization
│   └── populate_data.py # Sample data population
│
├── data/                 # SQLite database storage
├── logs/                 # Application logs
└── docker-compose.yml    # Container deployment
└── assets/             # Static files and data
```

## Development

This project follows modern Python best practices:

- **Modular Design**: Commands organized in cogs
- **Type Hints**: Full type annotation support
- **Async/Await**: Proper asynchronous programming
- **Error Handling**: Comprehensive error management
- **Logging**: Structured logging with different levels

### Development Commands

```bash
# Development setup with auto-formatting
make dev

# Run with hot reload
make run-dev

# Format code
make format

# Run tests
make check
```

### Additional Resources
- Check the detailed [Technical Wiki](TECHNICAL_WIKI.md) for in-depth documentation
- Review logs in `logs/bot.log` for troubleshooting
- Enable debug mode: set `DEBUG=true` in `.env`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the coding standards
4. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
