"""Configuration settings for Utils Bot v2.0"""

import os
from typing import List, Optional
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    """Bot configuration settings"""
    
    # Bot settings
    bot_token: str = os.getenv("BOT_TOKEN", "")
    bot_id: Optional[str] = os.getenv("BOT_ID") or os.getenv("APPLICATION_ID")
    bot_prefix: str = os.getenv("BOT_PREFIX", "!")
    bot_support_server: str = os.getenv("BOT_SUPPORT_SERVER", "")
    auto_sync_commands: bool = os.getenv("AUTO_SYNC_COMMANDS", "true").lower() == "true"
    
    # Developer settings
    dev_ids: List[int] = []
    dev_guild_id: int = int(os.getenv("DEV_GUILD_ID", "0"))
    closed_beta: bool = os.getenv("CLOSED_BETA", "false").lower() == "true"
    
    # Google Gemini
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/bot.log")
    log_max_bytes: int = int(os.getenv("LOG_MAX_BYTES", "10485760"))
    log_backup_count: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/bot.db")
    
    # External APIs
    screenshot_service_url: Optional[str] = os.getenv("SCREENSHOT_SERVICE_URL")
    screenshot_api_key: Optional[str] = os.getenv("SCREENSHOT_API_KEY")
    unshorten_api_url: Optional[str] = os.getenv("UNSHORTEN_API_URL")
    unshorten_api_secret: Optional[str] = os.getenv("UNSHORTEN_API_SECRET")
    rapidapi_key: Optional[str] = os.getenv("RAPIDAPI_KEY")
    
    # Monitoring
    sentry_dsn: Optional[str] = os.getenv("SENTRY_DSN")
    enable_metrics: bool = os.getenv("ENABLE_METRICS", "false").lower() == "true"
    
    # Rate limiting
    global_rate_limit: int = int(os.getenv("GLOBAL_RATE_LIMIT", "5"))
    cooldown_rate: int = int(os.getenv("COOLDOWN_RATE", "2"))
    
    # Features
    enable_games: bool = os.getenv("ENABLE_GAMES", "true").lower() == "true"
    enable_network_tools: bool = os.getenv("ENABLE_NETWORK_TOOLS", "true").lower() == "true"
    enable_ai_commands: bool = os.getenv("ENABLE_AI_COMMANDS", "true").lower() == "true"
    enable_system_commands: bool = os.getenv("ENABLE_SYSTEM_COMMANDS", "true").lower() == "true"
    
    # Cache
    redis_url: Optional[str] = os.getenv("REDIS_URL")
    cache_ttl: int = int(os.getenv("CACHE_TTL", "300"))
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "")
    session_timeout: int = int(os.getenv("SESSION_TIMEOUT", "3600"))
    
    # Development
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    auto_sync_commands: bool = os.getenv("AUTO_SYNC_COMMANDS", "false").lower() == "true"

    def __init__(self, **data):
        dev_ids_str = os.getenv("DEV_IDS", "")
        if dev_ids_str:
            try:
                dev_ids = [int(x.strip()) for x in dev_ids_str.split(",") if x.strip()]
            except ValueError:
                dev_ids = []
        else:
            dev_ids = []
        
        data.setdefault('dev_ids', dev_ids)
        super().__init__(**data)
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


settings = Settings()


class Assets:
    """Static asset URLs and constants"""
    
    # Bot branding
    BOT_AVATAR_URL = "https://cdn.discordapp.com/attachments/1143096931569107005/1169530235155386449/Presentation1.png"
    BOT_BANNER_URL = "https://media.discordapp.net/attachments/1143096931569107005/1169530235155386449/Presentation1.png"
    
    # External service icons
    GEMINI_ICON_URL = "https://ai.google.dev/static/site-assets/images/gemini-logo.svg"
    
    # Colors (Discord color scheme)
    PRIMARY_COLOR = 0x5865F2
    SUCCESS_COLOR = 0x00FF00
    ERROR_COLOR = 0xFF0000
    WARNING_COLOR = 0xFFFF00
    INFO_COLOR = 0x00FFFF
    
    # Version
    BOT_VERSION = "2.0.0"


assets = Assets()
