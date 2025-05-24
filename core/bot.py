"""
Core bot class for Utils Bot v2.0 - Slash Commands Only
"""

from pathlib import Path
from typing import List, Optional
import time

import discord
from discord.ext import commands

from config.settings import settings, assets
from core.logger import get_logger
from models.database import Database


class UtilsBot(commands.Bot):
    """
    Main bot class with slash commands only
    """
    
    def __init__(self):
        # Configure intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        
        # Initialize bot with disabled prefix commands
        super().__init__(
            command_prefix="$disabled$",  # Unused prefix - slash commands only
            intents=intents,
            help_command=None,
        )
        
        # Setup logging
        self.logger = get_logger(__name__)
        
        # Initialize database
        self.db: Optional[Database] = None
        
        # Bot metadata
        self.version = assets.BOT_VERSION
        self.start_time: Optional[float] = None
        
        # Cog management
        self.loaded_cogs: List[str] = []
    
    async def setup_hook(self) -> None:
        """Setup hook called when bot is starting up"""
        self.logger.info("Starting bot setup...")
        
        # Initialize database
        self.db = Database(settings.database_url)
        await self.db.initialize()
        
        # Load cogs
        await self.load_cogs()
        
        # Sync commands if enabled
        if settings.auto_sync_commands:
            await self.sync_commands()
        
        self.logger.info("Bot setup completed")
    
    async def load_cogs(self) -> None:
        """Load all available cogs"""
        cogs_dir = Path("cogs")
        if not cogs_dir.exists():
            self.logger.warning("Cogs directory not found")
            return
        
        for cog_file in cogs_dir.glob("*.py"):
            if cog_file.name.startswith("_"):
                continue
                
            cog_name = f"cogs.{cog_file.stem}"
            
            try:
                await self.load_extension(cog_name)
                self.loaded_cogs.append(cog_name)
                self.logger.info(f"Loaded cog: {cog_name}")
            except Exception as e:
                self.logger.error(f"Failed to load cog {cog_name}: {e}")
    
    async def sync_commands(self) -> None:
        """Sync application commands"""
        try:
            # Sync global commands
            synced = await self.tree.sync()
            self.logger.info(f"Synced {len(synced)} global commands")
            
            # Sync dev guild commands if specified
            if settings.dev_guild_id:
                dev_guild = discord.Object(id=settings.dev_guild_id)
                synced_dev = await self.tree.sync(guild=dev_guild)
                self.logger.info(f"Synced {len(synced_dev)} dev guild commands")
                
        except Exception as e:
            self.logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self) -> None:
        """Called when the bot is ready"""
        self.start_time = time.time()
        
        self.logger.info(
            f"Bot ready! Logged in as {self.user} (ID: {self.user.id}) | "
            f"Guilds: {len(self.guilds)} | Users: {len(self.users)} | "
            f"Slash Commands: {len(self.tree.get_commands())}"
        )
    
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Called when bot joins a guild"""
        self.logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
        
        # Update presence
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.guilds)} servers | v{self.version}"
        )
        await self.change_presence(activity=activity)
    
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """Called when bot leaves a guild"""
        self.logger.info(f"Left guild: {guild.name} (ID: {guild.id})")
        
        # Update presence
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.guilds)} servers | v{self.version}"
        )
        await self.change_presence(activity=activity)
    
    async def on_application_command_error(
        self, 
        interaction: discord.Interaction, 
        error: discord.app_commands.AppCommandError
    ) -> None:
        """Global application command error handler"""
        from utils.embeds import create_error_embed
        
        self.logger.error(
            f"Application command error: {error}",
            extra={
                "command": interaction.command.name if interaction.command else "Unknown",
                "user": str(interaction.user),
                "guild": str(interaction.guild) if interaction.guild else "DM",
            }
        )
        
        # Handle specific error types
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            embed = create_error_embed(
                "Command on Cooldown",
                f"This command is on cooldown. Try again in {error.retry_after:.1f} seconds."
            )
        elif isinstance(error, discord.app_commands.MissingPermissions):
            embed = create_error_embed(
                "Missing Permissions",
                "You don't have permission to use this command."
            )
        elif isinstance(error, discord.app_commands.BotMissingPermissions):
            embed = create_error_embed(
                "Bot Missing Permissions", 
                "I don't have the required permissions to execute this command."
            )
        else:
            embed = create_error_embed(
                "Command Error",
                "An unexpected error occurred while executing this command."
            )
        
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.NotFound:
            pass  # Interaction expired

    async def close(self) -> None:
        """Cleanup when bot is shutting down"""
        self.logger.info("Shutting down bot...")
        
        if self.db:
            await self.db.close()
        
        await super().close()
        self.logger.info("Bot shutdown complete")
    
    @property
    def uptime(self) -> Optional[float]:
        """Get bot uptime in seconds"""
        if self.start_time:
            return time.time() - self.start_time
        return None
