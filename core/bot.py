"""Core bot class for UtilsBot+ - Slash Commands Only"""

from pathlib import Path
from typing import List, Optional
import time

import discord
from discord.ext import commands, tasks

from config.settings import settings, assets
from core.logger import get_logger
from models.database import Database


class UtilsBotPlus(commands.Bot):
    """Main bot class with slash commands only"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        
        super().__init__(
            command_prefix="$disabled$",  # Unused prefix - slash commands only
            intents=intents,
            help_command=None,
        )
        
        self.logger = get_logger(__name__)
        
        self.db: Optional[Database] = None
        
        self.version = assets.BOT_VERSION
        self.start_time: Optional[float] = None
        
        self.loaded_cogs: List[str] = []
        
        # Status update task
        self.status_update_task = self.update_status_periodically.start()

    @tasks.loop(minutes=30)  # Update status every 30 minutes
    async def update_status_periodically(self) -> None:
        """Periodically update bot status for variety"""
        if self.is_ready():
            await self.update_bot_status()

    @update_status_periodically.before_loop
    async def before_status_update(self) -> None:
        """Wait until bot is ready before starting status updates"""
        await self.wait_until_ready()

    async def setup_hook(self) -> None:
        """Setup hook called when bot is starting up"""
        self.logger.info("Starting bot setup...")
        
        self.db = Database(settings.database_url)
        await self.db.initialize()
        
        await self.load_cogs()
        
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
            synced = await self.tree.sync()
            self.logger.info(f"Synced {len(synced)} global commands")
            
            if settings.dev_guild_id:
                dev_guild = discord.Object(id=settings.dev_guild_id)
                synced_dev = await self.tree.sync(guild=dev_guild)
                self.logger.info(f"Synced {len(synced_dev)} dev guild commands")
                
        except Exception as e:
            self.logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self) -> None:
        """Called when the bot is ready"""
        self.start_time = time.time()
        
        # Update bot status
        await self.update_bot_status()
        
        if self.user:
            self.logger.info(
                f"Bot ready! Logged in as {self.user} (ID: {self.user.id}) | "
                f"Guilds: {len(self.guilds)} | Users: {len(self.users)} | "
                f"Slash Commands: {len(self.tree.get_commands())}"
            )
    
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Called when bot joins a guild"""
        self.logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
        
        # Update status with new server count
        await self.update_bot_status()
    
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """Called when bot leaves a guild"""
        self.logger.info(f"Left guild: {guild.name} (ID: {guild.id})")
        
        # Update status with new server count
        await self.update_bot_status()
    
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
    
    async def update_bot_status(self) -> None:
        """Update bot's Discord status with current information"""
        try:
            total_guilds = len(self.guilds)
            total_users = len(self.users)
            total_commands = len(self.tree.get_commands())
            
            # Import here to avoid circular imports
            import random
            from datetime import datetime
            
            # Calculate uptime for display
            uptime_hours = 0
            if self.start_time:
                uptime_seconds = time.time() - self.start_time
                uptime_hours = int(uptime_seconds // 3600)
            
            # Create diverse status messages based on time and stats
            current_hour = datetime.now().hour
            
            # Define different status categories
            status_options = {
                "stats": [
                    f"{total_guilds} servers | v{self.version}",
                    f"{total_users:,} users | /help for commands",
                    f"{total_commands} slash commands available",
                    f"Serving {total_guilds} communities"
                ],
                "helpful": [
                    "Type /help for commands",
                    f"Ready to help in {total_guilds} servers",
                    "Use /info for bot information",
                    "AI-powered utilities at your service"
                ],
                "activity": [
                    f"Online for {uptime_hours}h | v{self.version}",
                    f"Processing commands in {total_guilds} servers",
                    f"Helping {total_users:,} Discord users",
                    "Providing utilities & AI assistance"
                ]
            }
            
            # Choose status category based on time (for variety)
            if current_hour < 8:  # Early morning - show stats
                category = "stats"
                activity_type = discord.ActivityType.watching
            elif current_hour < 16:  # Day time - show helpful info
                category = "helpful"
                activity_type = discord.ActivityType.listening
            else:  # Evening - show activity
                category = "activity"
                activity_type = discord.ActivityType.playing
            
            # Add some randomness while keeping time-based preference
            if random.random() < 0.3:  # 30% chance to use different category
                category = random.choice(list(status_options.keys()))
                activity_type = random.choice([
                    discord.ActivityType.watching,
                    discord.ActivityType.listening,
                    discord.ActivityType.playing
                ])
            
            # Select message from chosen category
            message = random.choice(status_options[category])
            
            # Special status for milestones
            if total_guilds % 50 == 0 and total_guilds > 0:
                message = f"🎉 {total_guilds} servers milestone! | v{self.version}"
                activity_type = discord.ActivityType.playing
            elif total_users >= 10000 and total_users % 1000 < 50:
                message = f"🎊 {total_users:,} users milestone! | /help"
                activity_type = discord.ActivityType.watching
            
            # Create and set the activity
            activity = discord.Activity(type=activity_type, name=message)
            await self.change_presence(activity=activity, status=discord.Status.online)
            
            self.logger.debug(f"Updated bot status: {activity_type.name} '{message}'")
            
        except Exception as e:
            self.logger.error(f"Failed to update bot status: {e}")
            # Fallback to simple status
            try:
                fallback_activity = discord.Activity(
                    type=discord.ActivityType.playing,
                    name=f"UtilsBot+ v{self.version}"
                )
                await self.change_presence(activity=fallback_activity, status=discord.Status.online)
            except Exception as fallback_error:
                self.logger.error(f"Fallback status update also failed: {fallback_error}")
