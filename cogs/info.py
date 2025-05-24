"""
Information and bot management cog for Utils Bot v2.0
"""

import platform
import psutil
import time
from typing import Optional, List

import discord
from discord import app_commands
from discord.ext import commands

from config.settings import settings, assets
from core.logger import get_logger
from utils.checks import dev_only, requires_whitelist
from utils.embeds import create_embed, create_success_embed, create_error_embed, format_duration


class InfoCog(commands.Cog, name="Info"):
    """Information and bot management commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)
    
    # Slash Commands Only
    
    @app_commands.command(name="info", description="Display bot information and statistics")
    async def info(self, interaction: discord.Interaction):
        """Display comprehensive bot information"""
        await interaction.response.defer()
        
        # Get system information
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        cpu_usage = process.cpu_percent()
        
        # Bot statistics
        total_guilds = len(self.bot.guilds)
        total_users = len(self.bot.users)
        total_commands = len(self.bot.tree.get_commands())
        uptime = self.bot.uptime
        
        embed = create_embed(
            f"🤖 {self.bot.user.display_name} Information",
            f"A modern Discord utility bot with {total_commands} commands",
            thumbnail=self.bot.user.display_avatar.url
        )
        
        # Bot Statistics
        embed.add_field(
            name="📊 Statistics",
            value=(
                f"**Servers:** {total_guilds:,}\n"
                f"**Users:** {total_users:,}\n"
                f"**Commands:** {total_commands}\n"
                f"**Uptime:** {format_duration(uptime) if uptime else 'Unknown'}"
            ),
            inline=True
        )
        
        # Technical Information
        embed.add_field(
            name="⚙️ Technical",
            value=(
                f"**Version:** {assets.BOT_VERSION}\n"
                f"**Discord.py:** {discord.__version__}\n"
                f"**Python:** {platform.python_version()}\n"
                f"**Platform:** {platform.system()}"
            ),
            inline=True
        )
        
        # Performance
        embed.add_field(
            name="📈 Performance",
            value=(
                f"**Memory:** {memory_usage:.1f} MB\n"
                f"**CPU:** {cpu_usage:.1f}%\n"
                f"**Latency:** {round(self.bot.latency * 1000)}ms\n"
                f"**Loaded Cogs:** {len(self.bot.loaded_cogs)}"
            ),
            inline=True
        )
        
        # Features
        features = []
        if settings.enable_ai_commands:
            features.append("🤖 AI Commands")
        if settings.enable_games:
            features.append("🎮 Games")
        if settings.enable_network_tools:
            features.append("🌐 Network Tools")
        if settings.enable_system_commands:
            features.append("🔧 System Commands")
        
        if features:
            embed.add_field(
                name="✨ Features",
                value="\n".join(features),
                inline=True
            )
        
        # Links and Support
        embed.add_field(
            name="🔗 Links",
            value=(
                f"**Support Server:** {settings.bot_support_server}\n"
                f"**Developer:** <@{settings.dev_ids[0]}>" if settings.dev_ids else "Unknown"
            ),
            inline=True
        )
        
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="ping", description="Check bot latency and response time")
    async def ping(self, interaction: discord.Interaction):
        """Check bot latency"""
        start_time = time.time()
        await interaction.response.defer()
        end_time = time.time()
        
        response_time = round((end_time - start_time) * 1000, 2)
        websocket_latency = round(self.bot.latency * 1000, 2)
        
        embed = create_embed(
            "🏓 Pong!",
            f"Bot latency and response times"
        )
        
        embed.add_field(
            name="Response Time",
            value=f"{response_time}ms",
            inline=True
        )
        
        embed.add_field(
            name="WebSocket Latency",
            value=f"{websocket_latency}ms",
            inline=True
        )
        
        # Color based on latency
        if websocket_latency < 100:
            embed.color = 0x00ff00  # Green - Excellent
        elif websocket_latency < 200:
            embed.color = 0xffaa00  # Yellow - Good
        else:
            embed.color = 0xff0000  # Red - Poor
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="version", description="Display bot version information")
    async def version(self, interaction: discord.Interaction):
        """Display version information"""
        embed = create_embed(
            f"📋 Version Information",
            f"**Bot Version:** {assets.BOT_VERSION}\n"
            f"**Discord.py Version:** {discord.__version__}\n"
            f"**Python Version:** {platform.python_version()}"
        )
        
        embed.add_field(
            name="🔄 Changelog",
            value=(
                "• Modern rewrite with improved architecture\n"
                "• Google Gemini AI integration\n" 
                "• Enhanced security and permissions\n"
                "• Improved error handling and logging\n"
                "• Database-backed user management"
            ),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    async def category_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete for help command categories"""
        categories = ["Information", "AI", "Games", "Tools", "Network", "System"]
        return [
            app_commands.Choice(name=category, value=category.lower())
            for category in categories
            if current.lower() in category.lower()
        ]

    @app_commands.command(name="help", description="View all available commands and their descriptions")
    @app_commands.describe(
        category="Filter commands by category (optional)",
        ephemeral="Whether to show the help only to you"
    )
    @app_commands.autocomplete(category=category_autocomplete)
    async def help_command(
        self, 
        interaction: discord.Interaction,
        category: Optional[str] = None,
        ephemeral: bool = False
    ):
        """Display help information for all commands"""
        
        # Get all commands from the bot's command tree
        all_commands = self.bot.tree.get_commands()
        
        # Organize commands by cog/category
        command_categories = {
            "Information": [],
            "AI": [],
            "Games": [],
            "Tools": [],
            "Network": [],
            "System": [],
            "Other": []
        }
        
        # Categorize commands
        for cmd in all_commands:
            if hasattr(cmd, 'binding') and cmd.binding:
                cog_name = getattr(cmd.binding, 'qualified_name', 'Other')
                
                # Map cog names to user-friendly categories
                if cog_name == "Info":
                    command_categories["Information"].append(cmd)
                elif cog_name == "AI":
                    command_categories["AI"].append(cmd)
                elif cog_name == "Games":
                    command_categories["Games"].append(cmd)
                elif cog_name == "Tools":
                    command_categories["Tools"].append(cmd)
                elif cog_name == "Network":
                    command_categories["Network"].append(cmd)
                elif cog_name == "System":
                    command_categories["System"].append(cmd)
                else:
                    command_categories["Other"].append(cmd)
            else:
                command_categories["Other"].append(cmd)
        
        # Filter by category if specified
        if category:
            category_key = category.title()
            if category_key not in command_categories:
                embed = create_error_embed(
                    "Invalid Category",
                    f"Available categories: {', '.join(command_categories.keys())}"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Show only the specified category
            filtered_categories = {category_key: command_categories[category_key]}
            command_categories = filtered_categories
        
        # Create help embed
        embed = create_embed(
            "🛠️ Bot Commands Help",
            f"Here are all available slash commands{f' in the **{category}** category' if category else ''}:",
            thumbnail=assets.BOT_AVATAR_URL
        )
        
        # Add fields for each category
        total_commands = 0
        for cat_name, commands in command_categories.items():
            if not commands:
                continue
                
            # Create command list for this category
            command_list = []
            for cmd in commands:
                # Handle both regular commands and groups
                if hasattr(cmd, 'commands') and cmd.commands:  # This is a group
                    # Add the group and its subcommands
                    command_list.append(f"**/{cmd.name}** - {cmd.description}")
                    for subcmd in cmd.commands:
                        command_list.append(f"  └ `/{cmd.name} {subcmd.name}` - {subcmd.description}")
                        total_commands += 1
                else:  # Regular command
                    command_list.append(f"`/{cmd.name}` - {cmd.description}")
                    total_commands += 1
            
            if command_list:
                # Split long command lists into multiple fields if needed
                command_text = "\n".join(command_list)
                if len(command_text) > 1024:
                    # Split into chunks
                    chunks = []
                    current_chunk = []
                    current_length = 0
                    
                    for cmd_line in command_list:
                        if current_length + len(cmd_line) + 1 > 1024:
                            chunks.append("\n".join(current_chunk))
                            current_chunk = [cmd_line]
                            current_length = len(cmd_line)
                        else:
                            current_chunk.append(cmd_line)
                            current_length += len(cmd_line) + 1
                    
                    if current_chunk:
                        chunks.append("\n".join(current_chunk))
                    
                    # Add fields for each chunk
                    for i, chunk in enumerate(chunks):
                        field_name = f"📂 {cat_name}" if i == 0 else f"📂 {cat_name} (cont.)"
                        embed.add_field(name=field_name, value=chunk, inline=False)
                else:
                    embed.add_field(name=f"📂 {cat_name}", value=command_text, inline=False)
        
        # Add footer with additional information
        embed.set_footer(
            text=f"Total commands: {total_commands} | Use /help <category> to filter by category"
        )
        
        # Add usage information
        if not category:
            embed.add_field(
                name="💡 How to Use",
                value=(
                    "• Type `/` to see all available commands\n"
                    "• Use `/help <category>` to filter commands\n"
                    "• Commands marked with 🔒 require special permissions\n"
                    "• Use `/info` for general bot information"
                ),
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    # Whitelist management commands
    whitelist_group = app_commands.Group(
        name="whitelist",
        description="Manage beta user whitelist (Developer only)"
    )
    
    @whitelist_group.command(name="add", description="Add user to beta whitelist")
    @app_commands.describe(user="User to add to whitelist")
    @dev_only()
    async def whitelist_add(self, interaction: discord.Interaction, user: discord.User):
        """Add a user to the beta whitelist"""
        if not self.bot.db:
            embed = create_error_embed(
                "Database Error",
                "Database is not available"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Get or create user
            db_user = await self.bot.db.get_or_create_user(user.id, user.display_name)
            
            if db_user.is_whitelisted:
                embed = create_error_embed(
                    "Already Whitelisted",
                    f"{user.mention} is already in the beta whitelist"
                )
            else:
                # Update whitelist status
                await self.bot.db.update_user_whitelist(user.id, True)
                embed = create_success_embed(
                    "User Whitelisted",
                    f"Successfully added {user.mention} to the beta whitelist"
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Whitelist add error: {e}")
            embed = create_error_embed(
                "Whitelist Error",
                "An error occurred while updating the whitelist"
            )
            await interaction.followup.send(embed=embed)
    
    @whitelist_group.command(name="remove", description="Remove user from beta whitelist")
    @app_commands.describe(user="User to remove from whitelist")
    @dev_only()
    async def whitelist_remove(self, interaction: discord.Interaction, user: discord.User):
        """Remove a user from the beta whitelist"""
        if not self.bot.db:
            embed = create_error_embed(
                "Database Error",
                "Database is not available"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Get user
            db_user = await self.bot.db.get_user(user.id)
            
            if not db_user or not db_user.is_whitelisted:
                embed = create_error_embed(
                    "Not Whitelisted",
                    f"{user.mention} is not in the beta whitelist"
                )
            else:
                # Update whitelist status
                await self.bot.db.update_user_whitelist(user.id, False)
                embed = create_success_embed(
                    "User Removed",
                    f"Successfully removed {user.mention} from the beta whitelist"
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Whitelist remove error: {e}")
            embed = create_error_embed(
                "Whitelist Error",
                "An error occurred while updating the whitelist"
            )
            await interaction.followup.send(embed=embed)
    
    @whitelist_group.command(name="list", description="List all whitelisted users")
    @dev_only()
    async def whitelist_list(self, interaction: discord.Interaction):
        """List all beta whitelisted users"""
        if not self.bot.db:
            embed = create_error_embed(
                "Database Error",
                "Database is not available"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            whitelisted_ids = await self.bot.db.get_whitelisted_users()
            
            if not whitelisted_ids:
                embed = create_embed(
                    "Beta Whitelist",
                    "No users are currently whitelisted for beta access"
                )
            else:
                user_list = []
                for user_id in whitelisted_ids:
                    try:
                        user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                        user_list.append(f"• {user.mention} ({user.display_name})")
                    except discord.NotFound:
                        user_list.append(f"• Unknown User ({user_id})")
                
                embed = create_embed(
                    f"Beta Whitelist ({len(user_list)} users)",
                    "\n".join(user_list[:20])  # Limit to 20 users to avoid embed limit
                )
                
                if len(user_list) > 20:
                    embed.add_field(
                        name="Notice",
                        value=f"Showing first 20 users. Total: {len(user_list)}",
                        inline=False
                    )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Whitelist list error: {e}")
            embed = create_error_embed(
                "Whitelist Error",
                "An error occurred while retrieving the whitelist"
            )
            await interaction.followup.send(embed=embed)
    
    @whitelist_group.command(name="check", description="Check if a user is whitelisted")
    @app_commands.describe(user="User to check")
    @dev_only()
    async def whitelist_check(self, interaction: discord.Interaction, user: discord.User):
        """Check if a user is in the beta whitelist"""
        if not self.bot.db:
            embed = create_error_embed(
                "Database Error",
                "Database is not available"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            db_user = await self.bot.db.get_user(user.id)
            
            if db_user and db_user.is_whitelisted:
                embed = create_success_embed(
                    "Whitelisted User",
                    f"{user.mention} is in the beta whitelist"
                )
            else:
                embed = create_embed(
                    "Not Whitelisted",
                    f"{user.mention} is not in the beta whitelist"
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Whitelist check error: {e}")
            embed = create_error_embed(
                "Check Error",
                "An error occurred while checking the whitelist"
            )
            await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(InfoCog(bot))
