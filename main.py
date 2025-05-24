"""
Main entry point for Utils Bot v2.0
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.bot import UtilsBot
from core.logger import setup_logging
from config.settings import settings


async def main():
    """Main bot entry point"""
    # Setup logging
    setup_logging()
    
    # Create and run bot
    bot = UtilsBot()
    
    try:
        await bot.start(settings.bot_token)
    except KeyboardInterrupt:
        await bot.close()
    except Exception as e:
        await bot.close()
        raise e


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
