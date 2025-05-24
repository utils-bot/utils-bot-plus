"""
System commands cog for Utils Bot v2.0
"""

import io
import sys
import traceback
from typing import Literal, Optional

import discord
from discord import app_commands
from discord.ext import commands

from core.logger import get_logger
from utils.checks import dev_only, is_developer
from utils.embeds import create_embed, create_success_embed, create_error_embed, PaginatedEmbed


class SystemCog(commands.Cog, name="System"):
    """System management and developer commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)
    
    @app_commands.command(name="sync", description="Sync slash commands (Developer only)")
    @app_commands.describe(
        scope="Where to sync commands",
        guild_id="Specific guild ID to sync to"
    )
    @app_commands.choices(scope=[
        app_commands.Choice(name="Global", value="global"),
        app_commands.Choice(name="Current Guild", value="guild"),
        app_commands.Choice(name="Specific Guild", value="specific")
    ])
    @dev_only()
    async def sync_commands(
        self, 
        interaction: discord.Interaction,
        scope: Literal["global", "guild", "specific"] = "global",
        guild_id: Optional[str] = None
    ):
        """Sync application commands"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            if scope == "global":
                synced = await self.bot.tree.sync()
                embed = create_success_embed(
                    "Commands Synced",
                    f"Synced {len(synced)} global commands"
                )
            
            elif scope == "guild":
                if not interaction.guild:
                    embed = create_error_embed(
                        "Error", 
                        "This command must be used in a guild for guild sync"
                    )
                else:
                    synced = await self.bot.tree.sync(guild=interaction.guild)
                    embed = create_success_embed(
                        "Commands Synced",
                        f"Synced {len(synced)} commands to {interaction.guild.name}"
                    )
            
            elif scope == "specific":
                if not guild_id:
                    embed = create_error_embed(
                        "Error",
                        "Guild ID is required for specific guild sync"
                    )
                else:
                    try:
                        guild = discord.Object(id=int(guild_id))
                        synced = await self.bot.tree.sync(guild=guild)
                        embed = create_success_embed(
                            "Commands Synced",
                            f"Synced {len(synced)} commands to guild {guild_id}"
                        )
                    except ValueError:
                        embed = create_error_embed(
                            "Error",
                            "Invalid guild ID provided"
                        )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Command sync failed: {e}")
            embed = create_error_embed(
                "Sync Failed",
                f"Failed to sync commands: {str(e)}"
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="eval", description="Execute Python code (Developer only)")
    @app_commands.describe(code="Python code to execute")
    @dev_only()
    async def evaluate_code(self, interaction: discord.Interaction, code: str):
        """Evaluate Python code"""
        await interaction.response.defer(ephemeral=True)
        
        # Setup execution environment
        env = {
            'bot': self.bot,
            'interaction': interaction,
            'discord': discord,
            'commands': commands,
            'guild': interaction.guild,
            'channel': interaction.channel,
            'user': interaction.user,
            'db': self.bot.db
        }
        
        # Capture stdout
        stdout = io.StringIO()
        old_stdout = sys.stdout
        
        try:
            # Redirect stdout
            sys.stdout = stdout
            
            # Execute code
            if code.startswith('```python'):
                code = code[9:-3]
            elif code.startswith('```'):
                code = code[3:-3]
            
            # Try to evaluate as expression first
            try:
                result = eval(code, env)
                if result is not None:
                    print(repr(result))
            except SyntaxError:
                # If not an expression, execute as statement
                exec(code, env)
            
            # Get output
            output = stdout.getvalue()
            
        except Exception as e:
            output = f"Error: {traceback.format_exc()}"
        
        finally:
            # Restore stdout
            sys.stdout = old_stdout
        
        # Format output
        if not output:
            output = "No output"
        
        # Truncate if too long
        if len(output) > 1900:
            output = output[:1900] + "\n... (truncated)"
        
        embed = create_embed(
            "Code Evaluation",
            f"```python\n{code}\n```\n**Output:**\n```\n{output}\n```",
            color=0x00ff00 if not output.startswith("Error:") else 0xff0000
        )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="guilds", description="List bot guilds (Developer only)")
    @dev_only()
    async def list_guilds(self, interaction: discord.Interaction):
        """List all guilds the bot is in"""
        await interaction.response.defer(ephemeral=True)
        
        guilds = []
        for guild in self.bot.guilds:
            member_count = guild.member_count or 0
            guilds.append(f"**{guild.name}** (ID: {guild.id}) - {member_count:,} members")
        
        if not guilds:
            embed = create_embed("No Guilds", "Bot is not in any guilds")
        else:
            paginated = PaginatedEmbed(
                pages=guilds,
                title=f"Bot Guilds ({len(guilds)} total)",
                per_page=10
            )
            embed = paginated.get_embed()
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="reload", description="Reload a cog (Developer only)")
    @app_commands.describe(cog="Name of the cog to reload")
    @dev_only()
    async def reload_cog(self, interaction: discord.Interaction, cog: str):
        """Reload a specific cog"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            cog_name = f"cogs.{cog}" if not cog.startswith("cogs.") else cog
            await self.bot.reload_extension(cog_name)
            
            embed = create_success_embed(
                "Cog Reloaded",
                f"Successfully reloaded `{cog_name}`"
            )
        
        except commands.ExtensionNotLoaded:
            embed = create_error_embed(
                "Cog Not Loaded",
                f"Cog `{cog}` is not currently loaded"
            )
        
        except commands.ExtensionNotFound:
            embed = create_error_embed(
                "Cog Not Found",
                f"Cog `{cog}` could not be found"
            )
        
        except Exception as e:
            embed = create_error_embed(
                "Reload Failed",
                f"Failed to reload `{cog}`: {str(e)}"
            )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="load", description="Load a cog (Developer only)")
    @app_commands.describe(cog="Name of the cog to load")
    @dev_only()
    async def load_cog(self, interaction: discord.Interaction, cog: str):
        """Load a specific cog"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            cog_name = f"cogs.{cog}" if not cog.startswith("cogs.") else cog
            await self.bot.load_extension(cog_name)
            
            embed = create_success_embed(
                "Cog Loaded",
                f"Successfully loaded `{cog_name}`"
            )
        
        except commands.ExtensionAlreadyLoaded:
            embed = create_error_embed(
                "Cog Already Loaded",
                f"Cog `{cog}` is already loaded"
            )
        
        except commands.ExtensionNotFound:
            embed = create_error_embed(
                "Cog Not Found",
                f"Cog `{cog}` could not be found"
            )
        
        except Exception as e:
            embed = create_error_embed(
                "Load Failed",
                f"Failed to load `{cog}`: {str(e)}"
            )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="unload", description="Unload a cog (Developer only)")
    @app_commands.describe(cog="Name of the cog to unload")
    @dev_only()
    async def unload_cog(self, interaction: discord.Interaction, cog: str):
        """Unload a specific cog"""
        await interaction.response.defer(ephemeral=True)
        
        # Prevent unloading system cog
        if cog.lower() == "system":
            embed = create_error_embed(
                "Cannot Unload",
                "Cannot unload the system cog"
            )
            await interaction.followup.send(embed=embed)
            return
        
        try:
            cog_name = f"cogs.{cog}" if not cog.startswith("cogs.") else cog
            await self.bot.unload_extension(cog_name)
            
            embed = create_success_embed(
                "Cog Unloaded",
                f"Successfully unloaded `{cog_name}`"
            )
        
        except commands.ExtensionNotLoaded:
            embed = create_error_embed(
                "Cog Not Loaded",
                f"Cog `{cog}` is not currently loaded"
            )
        
        except Exception as e:
            embed = create_error_embed(
                "Unload Failed",
                f"Failed to unload `{cog}`: {str(e)}"
            )
        
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(SystemCog(bot))
