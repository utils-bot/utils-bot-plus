# Utils Bot v2.0

A modern, feature-rich Discord bot built with discord.py, providing utilities for servers including games, network tools, AI integration, and system management.

## Features

- 🎮 **Games**: Interactive Wordle implementation
- 🌐 **Network Tools**: Screenshot capture, URL unshortening, IP lookup
- 🤖 **AI Integration**: Google Gemini for intelligent responses
- 🔧 **System Commands**: Developer tools and bot management
- 🔐 **Security**: TOTP generation, user whitelisting
- 📊 **Monitoring**: Comprehensive logging and error tracking

## Setup

### Prerequisites

- Python 3.10 or higher
- Discord Bot Token
- Google Gemini API Key (free tier)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/utils-bot-v2.git
cd utils-bot-v2
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
# Production dependencies
pip install -r requirements.txt

# Or for development (includes testing and linting tools)
pip install -r requirements.txt -r requirements-dev.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
python migrations/init_db.py
```

6. Run the bot:
```bash
python main.py
```

### Development Setup

For development work, use the provided Makefile:

```bash
# Set up development environment
make setup

# Run tests
make test

# Format code
make format

# Run linting
make lint

# Run the bot in development mode
make run-dev
```

## Configuration

See `.env.example` for all available configuration options.

### Required Environment Variables

- `BOT_TOKEN`: Your Discord bot token
- `GEMINI_API_KEY`: Google Gemini API key
- `DEV_IDS`: Comma-separated list of developer Discord IDs
- `DEV_GUILD_ID`: Your development server ID

## Project Structure

```
utils-bot-v2/
├── main.py              # Bot entry point
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── config/             # Configuration management
├── core/               # Core bot functionality
├── cogs/               # Command modules (cogs)
├── utils/              # Utility functions
├── models/             # Data models
└── assets/             # Static files and data
```

## Development

This project follows modern Python best practices:

- **Modular Design**: Commands organized in cogs
- **Type Hints**: Full type annotation support
- **Async/Await**: Proper asynchronous programming
- **Error Handling**: Comprehensive error management
- **Logging**: Structured logging with different levels
- **Testing**: Unit tests for core functionality

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with proper tests
4. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
