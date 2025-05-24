"""
Health monitoring utilities for Utils Bot v2
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import aiohttp
from sqlalchemy import text

from core.logger import get_logger

logger = get_logger(__name__)


class HealthChecker:
    """Health checking system for monitoring bot status."""
    
    def __init__(self, bot):
        self.bot = bot
        self.checks: Dict[str, float] = {}
        self.last_check = datetime.utcnow()
        self.check_interval = 300  # 5 minutes
        
    async def check_database(self) -> bool:
        """Check database connectivity."""
        try:
            if hasattr(self.bot, 'db') and self.bot.db:
                async with self.bot.db.get_session() as session:
                    await session.execute(text("SELECT 1"))
                    return True
            return False
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def check_discord_api(self) -> bool:
        """Check Discord API connectivity."""
        try:
            # Simple check - get bot's own user info
            if self.bot.user:
                return True
            return False
        except Exception as e:
            logger.error(f"Discord API health check failed: {e}")
            return False
    
    async def check_external_apis(self) -> Dict[str, bool]:
        """Check external API endpoints."""
        results = {}
        
        # Check Google Gemini API (if configured)
        try:
            if hasattr(self.bot, 'gemini_client') and self.bot.gemini_client:
                # Simple API check - this would need to be implemented based on your client
                results['gemini'] = True
            else:
                results['gemini'] = False
        except Exception as e:
            logger.error(f"Gemini API health check failed: {e}")
            results['gemini'] = False
        
        # Check Redis (if configured)
        try:
            if hasattr(self.bot, 'redis') and self.bot.redis:
                await self.bot.redis.ping()
                results['redis'] = True
            else:
                results['redis'] = False
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            results['redis'] = False
        
        return results
    
    async def run_health_checks(self) -> Dict[str, any]:
        """Run all health checks and return results."""
        start_time = time.time()
        
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'bot_uptime': self.get_uptime(),
            'guild_count': len(self.bot.guilds),
            'user_count': sum(guild.member_count for guild in self.bot.guilds if guild.member_count),
            'latency': round(self.bot.latency * 1000, 2),  # ms
            'checks': {}
        }
        
        # Run individual checks
        results['checks']['database'] = await self.check_database()
        results['checks']['discord_api'] = await self.check_discord_api()
        results['checks']['external_apis'] = await self.check_external_apis()
        
        # Calculate check duration
        check_duration = time.time() - start_time
        results['check_duration_ms'] = round(check_duration * 1000, 2)
        
        # Overall health status
        all_critical_healthy = (
            results['checks']['database'] and 
            results['checks']['discord_api']
        )
        results['status'] = 'healthy' if all_critical_healthy else 'unhealthy'
        
        self.last_check = datetime.utcnow()
        logger.info(f"Health check completed: {results['status']}")
        
        return results
    
    def get_uptime(self) -> str:
        """Get bot uptime as a formatted string."""
        if hasattr(self.bot, 'start_time'):
            uptime = datetime.utcnow() - self.bot.start_time
            return str(uptime).split('.')[0]  # Remove microseconds
        return "Unknown"
    
    async def start_periodic_checks(self):
        """Start periodic health checks."""
        while True:
            try:
                await asyncio.sleep(self.check_interval)
                results = await self.run_health_checks()
                
                # Log warnings for failed checks
                if not results['checks']['database']:
                    logger.warning("Database health check failed")
                
                if not results['checks']['discord_api']:
                    logger.warning("Discord API health check failed")
                
                # You could implement alerting here
                # e.g., send webhook to monitoring service
                
            except Exception as e:
                logger.error(f"Periodic health check failed: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying


class MetricsCollector:
    """Collect and track bot metrics."""
    
    def __init__(self):
        self.metrics = {
            'commands_executed': 0,
            'errors_encountered': 0,
            'api_calls': 0,
            'response_times': [],
            'daily_stats': {}
        }
        self.start_time = datetime.utcnow()
    
    def increment_command_count(self):
        """Increment command execution counter."""
        self.metrics['commands_executed'] += 1
        
        # Track daily stats
        today = datetime.utcnow().date().isoformat()
        if today not in self.metrics['daily_stats']:
            self.metrics['daily_stats'][today] = {'commands': 0, 'errors': 0}
        self.metrics['daily_stats'][today]['commands'] += 1
    
    def increment_error_count(self):
        """Increment error counter."""
        self.metrics['errors_encountered'] += 1
        
        today = datetime.utcnow().date().isoformat()
        if today not in self.metrics['daily_stats']:
            self.metrics['daily_stats'][today] = {'commands': 0, 'errors': 0}
        self.metrics['daily_stats'][today]['errors'] += 1
    
    def add_response_time(self, duration_ms: float):
        """Add a response time measurement."""
        self.metrics['response_times'].append(duration_ms)
        
        # Keep only last 1000 measurements
        if len(self.metrics['response_times']) > 1000:
            self.metrics['response_times'] = self.metrics['response_times'][-1000:]
    
    def get_metrics_summary(self) -> Dict[str, any]:
        """Get a summary of current metrics."""
        response_times = self.metrics['response_times']
        
        summary = {
            'uptime': str(datetime.utcnow() - self.start_time).split('.')[0],
            'commands_executed': self.metrics['commands_executed'],
            'errors_encountered': self.metrics['errors_encountered'],
            'error_rate': self.metrics['errors_encountered'] / max(self.metrics['commands_executed'], 1),
            'api_calls': self.metrics['api_calls']
        }
        
        if response_times:
            summary['avg_response_time_ms'] = sum(response_times) / len(response_times)
            summary['min_response_time_ms'] = min(response_times)
            summary['max_response_time_ms'] = max(response_times)
        
        return summary
