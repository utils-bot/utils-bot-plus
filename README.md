# UtilsBot+

A modern, feature-rich Discord bot with AI integration, interactive games, network tools, security utilities, and developer commands—all through slash commands.

## ✨ Features

🤖 **AI-Powered**: Chat with Google Gemini directly in Discord  
🎮 **Interactive Games**: Play Wordle with friends  
🌐 **Network Tools**: Screenshots, IP lookup, URL expansion  
🔐 **Security Utilities**: 2FA codes, QR generation, password tools  
ℹ️ **Information**: Bot stats, help system, version info  
⚙️ **Developer Tools**: Command sync, code evaluation, hot reload  

## 📖 Documentation

For comprehensive guides, command examples, and detailed setup instructions, visit our **[GitHub Wiki](../../wiki)**:

- 🆕 **[For Users](../../wiki/3.-For-Users)** - Friendly guide to all commands
- 🚀 **[Quick Start](../../wiki/2.-Getting-Started)** - Setup in 5 minutes
- 🔧 **[Configuration](../../wiki/5.-Configuration-Guide)** - Detailed settings
- 👨‍💻 **[For Developers](../../wiki/8.-Development-Guide)** - Technical details

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ 
- [Discord Bot Token](https://discord.com/developers/applications)
- [Google Gemini API Key](https://aistudio.google.com/app/apikey) (free)

### Setup (5 minutes)
```bash
# 1. Clone and enter directory
git clone <your-repository-url>
cd utils-bot-plus

# 2. Run automated setup
chmod +x setup.sh && ./setup.sh

# 3. Install dependencies  
pip install -r requirements.txt

# 4. Configure .env file (edit with your tokens)
# BOT_TOKEN=your_discord_bot_token
# GEMINI_API_KEY=your_gemini_api_key
# DEV_IDS=your_discord_id

# 5. Initialize database and start
python migrations/init_db.py
python main.py
```

### First Steps
1. **Generate invite link**: Use `python generate_invite.py` or `/invite` command
2. Invite bot to your server with `applications.commands` scope
3. Use `/info` to verify bot is working
4. Try `/help` to see all available commands
5. Use `/sync` if commands don't appear

> 💡 **Tip**: Run `python generate_invite.py --help` for different permission levels

## 🛠️ Support

**Having issues?** Check our troubleshooting guides:
- **[Common Issues](../../wiki/6.-Troubleshooting)** - Setup problems and solutions
- **[Bot Won't Start](../../wiki/6.-Troubleshooting#bot-wont-start)** - Token and dependency issues  
- **[Commands Not Working](../../wiki/6.-Troubleshooting#commands-not-working)** - Permission fixes

**Need help?** Join our [Discord Server] (soon) or [open an issue](../../issues).

## 📋 Commands Overview

| Command | Description | Example |
|---------|-------------|---------|
| `/chat` | Chat with AI | `/chat message:"Hello!"` |
| `/wordle` | Play Wordle game | `/wordle` |
| `/screenshot` | Capture website | `/screenshot url:"google.com"` |
| `/totp` | Generate 2FA code | `/totp secret:"YOUR2FA"` |
| `/invite` | Generate bot invite | `/invite permissions:"recommended"` |
| `/info` | Bot statistics | `/info` |
| `/help` | Command help | `/help category:"AI"` |

[**See all commands →**](../../wiki/3.-For-Users)

## 🏗️ Technical Details

- **Language**: Python 3.11+ with discord.py 2.4+
- **Database**: SQLite with SQLAlchemy async ORM  
- **Architecture**: Modular cogs with slash commands only
- **APIs**: Google Gemini, ip-api, ScreenshotOne (optional)

For technical documentation, see:
- **[Architecture](../../wiki/8.-Development-Guide)** - Code structure and design
- **[API Reference](../../wiki/11.-API-Reference)** - Internal APIs
- **[Deployment](../../wiki/9.-Deployment-Guide)** - Production setup

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

<div align="center">

**[📖 Full Documentation](../../wiki)** • **[🚀 Quick Start](../../wiki/2.-Getting-Started)** • **[💬 User Guide](../../wiki/3.-For-Users)** • **[🐛 Issues](../../issues)**

</div>
