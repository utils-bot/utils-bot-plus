"""
Enhanced main entry point for UtilsBot+ with hosting service support
"""

import asyncio
import sys
import os
import signal
from pathlib import Path
from aiohttp import web
import aiohttp
import logging

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.bot import UtilsBotPlus
from core.logger import setup_logging
from config.settings import settings


class HostingServiceManager:
    """Manages the bot and health check server for hosting services"""
    
    def __init__(self):
        self.bot = None
        self.web_app = None
        self.site = None
        self.runner = None
        self.logger = logging.getLogger(__name__)
        
    async def create_health_app(self):
        """Create health check web application"""
        app = web.Application()
        
        async def health_check(request):
            """Health check endpoint"""
            bot_status = "running" if self.bot and not self.bot.is_closed() else "stopped"
            return web.json_response({
                "status": "healthy",
                "service": "utils-bot-plus",
                "bot_status": bot_status,
                "timestamp": __import__('time').time()
            })
        
        async def readiness_check(request):
            """Readiness check endpoint"""
            is_ready = self.bot and self.bot.is_ready() if self.bot else False
            status_code = 200 if is_ready else 503
            return web.json_response({
                "status": "ready" if is_ready else "not_ready",
                "service": "utils-bot-plus",
                "bot_ready": is_ready
            }, status=status_code)
        
        async def root_check(request):
            """Root endpoint check (some services check /)"""
            return web.json_response({
                "service": "utils-bot-plus",
                "status": "online",
                "version": "2.0"
            })
        
        app.router.add_get('/health', health_check)
        app.router.add_get('/ready', readiness_check)
        app.router.add_get('/', root_check)
        
        return app
    
    async def start_health_server(self):
        """Start the health check server"""
        port = int(os.getenv('PORT', 8080))
        
        try:
            self.web_app = await self.create_health_app()
            self.runner = web.AppRunner(self.web_app)
            await self.runner.setup()
            
            self.site = web.TCPSite(self.runner, '0.0.0.0', port)
            await self.site.start()
            
            self.logger.info(f"Health check server started on port {port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start health check server: {e}")
            return False
    
    async def stop_health_server(self):
        """Stop the health check server"""
        try:
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
            self.logger.info("Health check server stopped")
        except Exception as e:
            self.logger.error(f"Error stopping health check server: {e}")
    
    async def start_bot(self):
        """Start the Discord bot"""
        try:
            self.bot = UtilsBotPlus()
            self.logger.info("Starting Discord bot...")
            await self.bot.start(settings.bot_token)
        except Exception as e:
            self.logger.error(f"Failed to start bot: {e}")
            raise e
    
    async def stop_bot(self):
        """Stop the Discord bot"""
        try:
            if self.bot and not self.bot.is_closed():
                await self.bot.close()
                self.logger.info("Discord bot stopped")
        except Exception as e:
            self.logger.error(f"Error stopping bot: {e}")
    
    async def run(self):
        """Run both the bot and health check server"""
        try:
            # Start health check server first (hosting services need this)
            health_started = await self.start_health_server()
            if not health_started:
                self.logger.warning("Health check server failed to start, continuing with bot only")
            
            # Start the Discord bot
            await self.start_bot()
            
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            raise e
        finally:
            # Cleanup
            await self.stop_bot()
            await self.stop_health_server()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}")
            # Create new event loop for cleanup if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Schedule cleanup
            if not loop.is_closed():
                loop.create_task(self.cleanup())
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.stop_bot()
        await self.stop_health_server()


async def main():
    """Main entry point with hosting service support"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Check if we're in a hosting service environment
    is_hosted = os.getenv('PORT') is not None or os.getenv('RENDER') is not None
    
    if is_hosted:
        logger.info("Detected hosting service environment")
        # Use the hosting service manager
        manager = HostingServiceManager()
        manager.setup_signal_handlers()
        await manager.run()
    else:
        logger.info("Running in local/development mode")
        # Traditional bot-only mode
        bot = UtilsBotPlus()
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
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)
