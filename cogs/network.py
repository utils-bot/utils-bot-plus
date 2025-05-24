"""
Network utilities cog for Utils Bot v2.0
"""

import io
import ipaddress
from typing import Optional, Dict, Any
from urllib.parse import urlparse

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

try:
    from config.settings import settings
except ImportError:
    class Settings:
        enable_network_tools = True
    settings = Settings()

try:
    from core.logger import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

try:
    from utils.checks import requires_whitelist, cooldown
except ImportError:
    def requires_whitelist():
        def decorator(func):
            return func
        return decorator
    
    def cooldown(rate, per):
        def decorator(func):
            _ = rate  # Suppress unused argument warning
            _ = per   # Suppress unused argument warning
            return func
        return decorator

try:
    from utils.embeds import create_embed, create_error_embed, create_loading_embed, create_success_embed
except ImportError:
    def create_embed(title, description="", color=0x00ff00):
        embed = discord.Embed(title=title, description=description, color=color)
        return embed
    
    def create_error_embed(title, description):
        embed = discord.Embed(title=title, description=description, color=0xff0000)
        return embed
    
    def create_loading_embed(title, description):
        embed = discord.Embed(title=title, description=description, color=0xffaa00)
        return embed
    
    def create_success_embed(title, description):
        embed = discord.Embed(title=title, description=description, color=0x00ff00)
        return embed

try:
    from utils.screenshot import ScreenshotService
except ImportError:
    class ScreenshotService:
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
        
        async def capture_screenshot(self, url, full_page=False, width=1920, height=1080, wait_time=2):
            _ = url        # Suppress unused argument warning
            _ = full_page  # Suppress unused argument warning
            _ = width      # Suppress unused argument warning
            _ = height     # Suppress unused argument warning
            _ = wait_time  # Suppress unused argument warning
            return None


class NetworkCog(commands.Cog):
    """Network utility commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def cog_load(self):
        """Initialize HTTP session"""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def cog_unload(self):
        """Cleanup HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    @app_commands.command(name="screenshot", description="Take a screenshot of a website")
    @app_commands.describe(
        url="Website URL to screenshot",
        full_page="Capture full page (default: viewport only)",
        ephemeral="Whether to show the response only to you"
    )
    @requires_whitelist()
    @cooldown(rate=2, per=60)
    async def screenshot(
        self,
        interaction: discord.Interaction,
        url: str,
        full_page: bool = False,
        ephemeral: bool = False
    ):
        """Take a screenshot of a website"""
        # Validate URL
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                raise ValueError("Invalid URL")
        except Exception:
            embed = create_error_embed(
                "Invalid URL",
                "Please provide a valid website URL"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        loading_embed = create_loading_embed(
            "Taking Screenshot...",
            f"Capturing screenshot of `{url}`"
        )
        await interaction.response.send_message(embed=loading_embed, ephemeral=ephemeral)
        
        try:
            # Use the screenshot service
            async with ScreenshotService() as screenshot_service:
                screenshot_data = await screenshot_service.capture_screenshot(
                    url=url,
                    full_page=full_page,
                    width=1920,
                    height=1080,
                    wait_time=2
                )
            
            if screenshot_data:
                file = discord.File(io.BytesIO(screenshot_data), filename="screenshot.png")
                embed = create_success_embed(
                    "Screenshot Captured",
                    f"Screenshot of **{parsed.netloc}**"
                )
                embed.set_image(url="attachment://screenshot.png")
                
                await interaction.edit_original_response(embed=embed, attachments=[file])
                
                # Track API usage
                if hasattr(self.bot, 'db') and self.bot.db:
                    await self.bot.db.track_api_usage(interaction.user.id, "screenshot")
            else:
                embed = create_error_embed(
                    "Screenshot Failed",
                    "Could not capture screenshot. The website might be inaccessible or blocking requests."
                )
                await interaction.edit_original_response(embed=embed)
                
        except Exception as e:
            self.logger.error("Screenshot error for %s: %s", url, e)
            embed = create_error_embed(
                "Screenshot Error",
                "An error occurred while taking the screenshot"
            )
            await interaction.edit_original_response(embed=embed)
    
    async def _take_screenshot_api(self, url: str, full_page: bool) -> Optional[bytes]:
        """Take screenshot using external API - deprecated, use ScreenshotService instead"""
        # This method is kept for backward compatibility but should not be used
        _ = url  # Suppress unused argument warning
        _ = full_page  # Suppress unused argument warning
        return None
    
    @app_commands.command(name="ip", description="Get information about an IP address")
    @app_commands.describe(
        ip="IP address to lookup",
        ephemeral="Whether to show the response only to you"
    )
    @requires_whitelist()
    @cooldown(rate=5, per=60)
    async def ip_lookup(
        self,
        interaction: discord.Interaction,
        ip: str,
        ephemeral: bool = False
    ):
        """Get detailed information about an IP address"""
        # Validate IP address
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private:
                embed = create_error_embed(
                    "Private IP Address",
                    "Cannot lookup information for private IP addresses"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        except ValueError:
            embed = create_error_embed(
                "Invalid IP Address",
                "Please provide a valid IP address"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        loading_embed = create_loading_embed(
            "Looking up IP...",
            f"Gathering information for `{ip}`"
        )
        await interaction.response.send_message(embed=loading_embed, ephemeral=ephemeral)
        
        try:
            # Use ip-api.com (free service)
            ip_info = await self._get_ip_info(ip)
            
            if ip_info and ip_info.get("status") == "success":
                embed = create_embed(
                    f"IP Information: {ip}",
                    color=0x00ff00
                )
                
                # Add fields with available information
                fields = [
                    ("Country", ip_info.get("country", "Unknown")),
                    ("Region", ip_info.get("regionName", "Unknown")),
                    ("City", ip_info.get("city", "Unknown")),
                    ("ISP", ip_info.get("isp", "Unknown")),
                    ("Organization", ip_info.get("org", "Unknown")),
                    ("Timezone", ip_info.get("timezone", "Unknown")),
                    ("Coordinates", f"{ip_info.get('lat', 'N/A')}, {ip_info.get('lon', 'N/A')}"),
                ]
                
                for name, value in fields:
                    if value and value != "Unknown":
                        embed.add_field(name=name, value=value, inline=True)
                
                # Add flag emoji if country code available
                country_code = ip_info.get("countryCode")
                if country_code:
                    embed.set_thumbnail(url=f"https://flagcdn.com/w80/{country_code.lower()}.png")
                
                await interaction.edit_original_response(embed=embed)
                
                # Track API usage
                if self.bot.db:
                    await self.bot.db.track_api_usage(interaction.user.id, "ip_lookup")
            else:
                embed = create_error_embed(
                    "Lookup Failed",
                    "Could not retrieve information for this IP address"
                )
                await interaction.edit_original_response(embed=embed)
                
        except Exception as e:
            self.logger.error(f"IP lookup error for {ip}: {e}")
            embed = create_error_embed(
                "Lookup Error",
                "An error occurred while looking up the IP address"
            )
            await interaction.edit_original_response(embed=embed)
    
    async def _get_ip_info(self, ip: str) -> Optional[Dict[str, Any]]:
        """Get IP information from ip-api.com"""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        
        try:
            url = f"http://ip-api.com/json/{ip}"
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            self.logger.error("IP API error: %s", e)
        
        return None
    
    @app_commands.command(name="unshorten", description="Expand shortened URLs")
    @app_commands.describe(
        url="Shortened URL to expand",
        ephemeral="Whether to show the response only to you"
    )
    @requires_whitelist()
    @cooldown(rate=5, per=60)
    async def unshorten_url(
        self,
        interaction: discord.Interaction,
        url: str,
        ephemeral: bool = False
    ):
        """Expand shortened URLs to reveal their destination"""
        # Validate URL
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                raise ValueError("Invalid URL")
        except Exception:
            embed = create_error_embed(
                "Invalid URL",
                "Please provide a valid URL"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        loading_embed = create_loading_embed(
            "Expanding URL...",
            f"Following redirects for `{url}`"
        )
        await interaction.response.send_message(embed=loading_embed, ephemeral=ephemeral)
        
        try:
            final_url = await self._follow_redirects(url)
            
            if final_url and final_url != url:
                embed = create_success_embed(
                    "URL Expanded",
                    f"**Original:** `{url}`\n**Expanded:** `{final_url}`"
                )
                
                # Add safety warning if suspicious
                if await self._is_suspicious_domain(final_url):
                    embed.add_field(
                        name="⚠️ Safety Warning",
                        value="This URL leads to a potentially suspicious domain. Proceed with caution.",
                        inline=False
                    )
                    embed.color = 0xffaa00
                
            elif final_url == url:
                embed = create_embed(
                    "URL Not Shortened",
                    f"This URL doesn't appear to be shortened: `{url}`"
                )
            else:
                embed = create_error_embed(
                    "Expansion Failed",
                    "Could not expand this URL. It might be invalid or inaccessible."
                )
            
            await interaction.edit_original_response(embed=embed)
            
            # Track API usage
            if self.bot.db:
                await self.bot.db.track_api_usage(interaction.user.id, "unshorten")
                
        except Exception as e:
            self.logger.error("URL unshorten error for %s: %s", url, e)
            embed = create_error_embed(
                "Expansion Error",
                "An error occurred while expanding the URL"
            )
            await interaction.edit_original_response(embed=embed)
    
    async def _follow_redirects(self, url: str, max_redirects: int = 10) -> Optional[str]:
        """Follow URL redirects to find final destination"""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.head(
                url,
                allow_redirects=True,
                max_redirects=max_redirects,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return str(response.url)
        except Exception as e:
            self.logger.error("Redirect following error: %s", e)
            return None
    
    async def _is_suspicious_domain(self, url: str) -> bool:
        """Check if domain might be suspicious (basic check)"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Basic suspicious indicators
            suspicious_tlds = ['.tk', '.ml', '.ga', '.cf']
            suspicious_keywords = ['bit.ly', 'tinyurl', 'suspicious', 'phishing']
            
            return (
                any(domain.endswith(tld) for tld in suspicious_tlds) or
                any(keyword in domain for keyword in suspicious_keywords) or
                len(domain.split('.')[0]) > 20  # Very long subdomain
            )
        except Exception:
            return False
    
    @app_commands.command(name="ping_bot", description="Check bot latency")
    async def ping_bot(self, interaction: discord.Interaction):
        """Check bot latency"""
        import time
        
        start_time = time.time()
        await interaction.response.defer()
        end_time = time.time()
        
        latency = round((end_time - start_time) * 1000, 2)
        ws_latency = round(self.bot.latency * 1000, 2)
        
        embed = create_embed(
            "🏓 Pong!",
            f"**Response Time:** {latency}ms\n**WebSocket Latency:** {ws_latency}ms"
        )
        
        # Color based on latency
        if ws_latency < 100:
            embed.color = 0x00ff00  # Green
        elif ws_latency < 200:
            embed.color = 0xffaa00  # Yellow
        else:
            embed.color = 0xff0000  # Red
        
        await interaction.followup.send(embed=embed)


async def setup(bot):
    if settings.enable_network_tools:
        await bot.add_cog(NetworkCog(bot))
