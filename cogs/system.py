"""System commands cog for UtilsBot+"""

import io
import sys
import traceback
from typing import Literal, Optional

import discord
from discord import app_commands
from discord.ext import commands

from core.logger import get_logger
from utils.checks import dev_only
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
        
        embed = None  # Initialize embed variable
        
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
    
    @app_commands.command(name="eval", description="Execute Python code in secure sandbox (Developer only)")
    @app_commands.describe(
        code="Python code to execute (optional if uploading file)",
        stdin_input="Optional input for the program (stdin)",
        file="Upload a Python file to execute",
        legacy_mode="Use legacy unsafe mode (not recommended)"
    )
    @dev_only()
    async def evaluate_code(
        self, 
        interaction: discord.Interaction, 
        code: str = "",
        stdin_input: str = "",
        file: Optional[discord.Attachment] = None,
        legacy_mode: bool = False
    ):
        """Execute Python code in a secure sandbox"""
        await interaction.response.defer(ephemeral=True)
        
        # Handle file upload
        main_code_from_file = None
        
        if file:
            # Validate file size (1MB limit)
            if file.size > 1024 * 1024:
                embed = create_embed(
                    "📁 File Too Large",
                    f"File `{file.filename}` exceeds the 1MB size limit. Current size: {self._format_file_size(file.size)}",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Check file type
            if not file.filename.endswith(('.py', '.txt')):
                embed = create_embed(
                    "📁 Unsupported File Type",
                    f"File `{file.filename}` is not supported. Please upload a `.py` or `.txt` file.",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed)
                return
            
            try:
                file_content = await file.read()
                main_code_from_file = file_content.decode('utf-8')
                
                # Provide feedback about file processing
                processing_embed = create_embed(
                    "📁 Processing File",
                    f"Processing uploaded file: `{file.filename}` ({self._format_file_size(file.size)})",
                    color=0x3498db
                )
                await interaction.followup.send(embed=processing_embed, ephemeral=True)
                
            except UnicodeDecodeError:
                embed = create_embed(
                    "📁 File Error",
                    f"Could not decode file `{file.filename}` as text. Please ensure it's a valid Python or text file.",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed)
                return
            except Exception as e:
                embed = create_embed(
                    "📁 File Error", 
                    f"Error reading file `{file.filename}`: {str(e)}",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed)
                return
        
        # Determine final code to execute
        final_code = ""
        if main_code_from_file and not code.strip():
            # Use uploaded file code when no code parameter provided or it's blank
            final_code = main_code_from_file
        elif main_code_from_file and code.strip():
            # Combine both when both are provided
            final_code = f"# Code from parameter:\n{code}\n\n# Code from uploaded file ({file.filename if file else 'unknown'}):\n{main_code_from_file}"
        elif code.strip():
            # Use only code parameter
            final_code = code
        else:
            # No code provided anywhere
            embed = create_embed(
                "❌ No Code Provided",
                "Please provide code to execute either by typing it in the code field or uploading a Python file.",
                color=0xff6b6b
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Clean code block formatting from the final code
        if final_code.startswith('```python'):
            final_code = final_code[9:-3]
        elif final_code.startswith('```'):
            final_code = final_code[3:-3]
        
        final_code = final_code.strip()
        
        if legacy_mode:
            # Legacy unsafe mode (for backwards compatibility)
            result = await self._legacy_eval(final_code, interaction)
        else:
            # Secure sandbox mode
            result = await self._secure_eval(final_code, stdin_input, interaction, file)
        
        await interaction.followup.send(embed=result)
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f}MB"

    async def _secure_eval(self, code: str, stdin_input: str, interaction: discord.Interaction, file: Optional[discord.Attachment] = None):
        """Execute code in secure sandbox"""
        try:
            from utils.sandboxing import execute_code_safely
            
            # Handle file attachments
            files = {}
            
            # Handle direct file attachment from command parameter
            if file:
                if file.size <= 1024 * 1024:  # 1MB limit
                    try:
                        file_content = await file.read()
                        files[file.filename] = file_content
                        self.logger.info(f"Processing attachment: {file.filename} ({file.size} bytes)")
                    except Exception as e:
                        return create_embed(
                            "📁 File Error",
                            f"Failed to read attachment `{file.filename}`: {str(e)}",
                            color=0xff6b6b
                        )
                else:
                    return create_embed(
                        "📁 File Error",
                        f"Attachment `{file.filename}` exceeds the 1MB size limit",
                        color=0xff6b6b
                    )
            
            # Execute in sandbox
            result = await execute_code_safely(code, files, stdin_input)
            
            # Format result with enhanced file information
            if result.success:
                output = result.output if result.output else "No output"
                
                # Build execution stats
                stats = [f"⏱️ **Execution Time:** {result.execution_time:.3f}s"]
                
                # Add file upload information
                if files:
                    file_info = []
                    for filename, content in files.items():
                        size = len(content) if isinstance(content, (str, bytes)) else len(str(content))
                        file_info.append(f"`{filename}` ({self._format_file_size(size)})")
                    stats.append(f"📤 **Files Uploaded:** {', '.join(file_info)}")
                
                # Add files created during execution
                if result.files_created:
                    stats.append(f"📁 **Files Created:** {', '.join(result.files_created)}")
                
                # Add memory usage if available
                if result.memory_used:
                    stats.append(f"💾 **Memory Used:** {result.memory_used}")
                
                embed = create_embed(
                    "✅ Code Executed Successfully",
                    f"```\n{output[:1800]}\n```",  # Limit output length
                    color=0x00ff00
                )
                embed.add_field(
                    name="📊 Execution Details",
                    value="\n".join(stats),
                    inline=False
                )
                
                # If output is too long, note truncation
                if len(output) > 1800:
                    embed.add_field(
                        name="⚠️ Note",
                        value="Output was truncated due to length limits",
                        inline=False
                    )
                
                return embed
            else:
                embed = create_embed(
                    "❌ Execution Failed",
                    f"```\n{result.error[:1800]}\n```",
                    color=0xff6b6b
                )
                embed.add_field(
                    name="⏱️ Execution Time",
                    value=f"{result.execution_time:.3f}s",
                    inline=True
                )
                
                if files:
                    file_info = []
                    for filename, content in files.items():
                        size = len(content) if isinstance(content, (str, bytes)) else len(str(content))
                        file_info.append(f"`{filename}` ({self._format_file_size(size)})")
                    embed.add_field(
                        name="📤 Files Uploaded",
                        value=", ".join(file_info),
                        inline=False
                    )
                
                return embed
                
        except ImportError:
            return create_embed(
                "❌ Sandbox Not Available",
                "Secure execution is not available. The sandboxing module could not be imported.",
                color=0xff6b6b
            )
        except Exception as e:
            self.logger.error(f"Error in secure eval: {str(e)}")
            return create_embed(
                "❌ Execution Error",
                f"An unexpected error occurred: {str(e)}",
                color=0xff6b6b
            )
    
    async def _legacy_eval(self, code: str, interaction: discord.Interaction):
        """Legacy unsafe eval mode"""
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
        
        stdout = io.StringIO()
        old_stdout = sys.stdout
        
        try:
            sys.stdout = stdout
            
            try:
                result = eval(code, env)
                if result is not None:
                    print(repr(result))
            except SyntaxError:
                exec(code, env)
            
            output = stdout.getvalue()
            
        except Exception:
            output = f"Error: {traceback.format_exc()}"
        
        finally:
            sys.stdout = old_stdout
        
        if not output:
            output = "No output"
        
        if len(output) > 1900:
            output = output[:1900] + "\n... (truncated)"
        
        return create_embed(
            "⚠️ Legacy Code Evaluation (UNSAFE)",
            f"```python\n{code}\n```\n**Output:**\n```\n{output}\n```",
            color=0xfeca57 if not output.startswith("Error:") else 0xff6b6b
        )
    
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
    
    @app_commands.command(name="run", description="Run code with file uploads and input/output (Developer only)")
    @app_commands.describe(
        code="Code to execute (supports Python, C++, Java, etc.) - optional if uploading file",
        language="Programming language (auto-detected if not specified)",
        input_data="Input data for the program",
        timeout="Execution timeout in seconds (max 30)",
        file="Upload a source code file to execute"
    )
    @dev_only()
    async def run_code(
        self, 
        interaction: discord.Interaction, 
        code: str = "",
        language: str = "python",
        input_data: str = "",
        timeout: int = 10,
        file: Optional[discord.Attachment] = None
    ):
        """Run code with competitive programming support"""
        await interaction.response.defer(ephemeral=True)
        
        # Validate timeout
        timeout = min(max(timeout, 1), 30)  # Clamp between 1-30 seconds
        
        # Handle file uploads
        files = {}
        main_code = code
        main_code_from_file = None
        
        # Process file upload parameter
        if file:
            # Validate file size (5MB limit for run command)
            if file.size > 5 * 1024 * 1024:
                embed = create_embed(
                    "📁 File Too Large",
                    f"File `{file.filename}` exceeds the 5MB size limit. Current size: {self._format_file_size(file.size)}",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed)
                return
            
            try:
                file_content = await file.read()
                files[file.filename] = file_content
                
                # If this looks like a source file, use it as main code
                if self._is_source_file(file.filename):
                    main_code_from_file = file_content.decode('utf-8', errors='ignore')
                    detected_lang = self._detect_language(file.filename)
                    if detected_lang != "unknown":
                        language = detected_lang
                
                # Provide feedback about file processing
                processing_embed = create_embed(
                    "📁 Processing File",
                    f"Processing uploaded file: `{file.filename}` ({self._format_file_size(file.size)})",
                    color=0x3498db
                )
                await interaction.followup.send(embed=processing_embed, ephemeral=True)
                
            except Exception as e:
                embed = create_embed(
                    "📁 File Error",
                    f"Failed to read `{file.filename}`: {str(e)}",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed)
                return
        
        # Determine final code to execute
        if main_code_from_file and not main_code.strip():
            # Use uploaded file code when no code parameter provided or it's blank
            main_code = main_code_from_file
        elif main_code_from_file and main_code.strip():
            # Combine both when both are provided
            main_code = f"# Code from parameter:\n{main_code}\n\n# Code from uploaded file ({file.filename if file else 'unknown'}):\n{main_code_from_file}"
        # If only code parameter is provided, use it as-is (main_code already set)
        
        # Legacy support: check message attachments (for backwards compatibility)
        if not file and interaction.message and interaction.message.attachments:
            for attachment in interaction.message.attachments:
                if attachment.size > 5 * 1024 * 1024:  # 5MB limit
                    embed = create_embed(
                        "📁 File Too Large",
                        f"File `{attachment.filename}` is too large (max 5MB)",
                        color=0xff6b6b
                    )
                    await interaction.followup.send(embed=embed)
                    return
                
                try:
                    file_content = await attachment.read()
                    filename = attachment.filename
                    files[filename] = file_content
                    
                    # If no code provided and this looks like a source file, use it as main code
                    if not main_code.strip() and self._is_source_file(filename):
                        main_code = file_content.decode('utf-8', errors='ignore')
                        language = self._detect_language(filename)
                        
                except Exception as e:
                    embed = create_embed(
                        "📁 File Error",
                        f"Failed to read `{attachment.filename}`: {str(e)}",
                        color=0xff6b6b
                    )
                    await interaction.followup.send(embed=embed)
                    return
                    return
        
        if not main_code.strip():
            embed = create_embed(
                "❌ No Code Provided",
                "Please provide code to execute or attach a source code file.",
                color=0xff6b6b
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Clean code block formatting
        if main_code.startswith('```'):
            lines = main_code.split('\n')
            if len(lines) > 1:
                main_code = '\n'.join(lines[1:-1])
        
        # Execute code
        try:
            from utils.sandboxing import execute_code_safely, SandboxConfig
            
            # Configure sandbox for competitive programming
            config = SandboxConfig(
                timeout=timeout,
                memory_limit="256m",  # More memory for competitive programming
                cpu_limit=1.0,       # Full CPU access
                max_output_size=16384,  # More output for test cases
                max_file_size=5 * 1024 * 1024  # 5MB files
            )
            
            # Execute with language-specific handling
            if language.lower() in ['python', 'py']:
                result = await execute_code_safely(main_code, files, input_data, config)
            else:
                # For other languages, we'll need to compile first
                result = await self._execute_compiled_language(main_code, language, files, input_data)
            
            # Format competitive programming result
            embed = await self._format_cp_result(result, main_code, language, input_data, timeout)
            await interaction.followup.send(embed=embed)
            
        except ImportError:
            embed = create_embed(
                "⚠️ Sandbox Unavailable",
                "Secure sandbox is not available. Please install Docker to use this feature.",
                color=0xfeca57
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = create_embed(
                "🚨 Execution Error",
                f"Failed to execute code: {str(e)}",
                color=0xff6b6b
            )
            await interaction.followup.send(embed=embed)
    
    def _is_source_file(self, filename: str) -> bool:
        """Check if file is a source code file"""
        extensions = ['.py', '.cpp', '.cc', '.cxx', '.c', '.java', '.js', '.ts', '.go', '.rs', '.rb']
        return any(filename.lower().endswith(ext) for ext in extensions)
    
    def _detect_language(self, filename: str) -> str:
        """Detect programming language from filename"""
        filename = filename.lower()
        if filename.endswith('.py'):
            return 'python'
        elif filename.endswith(('.cpp', '.cc', '.cxx')):
            return 'cpp'
        elif filename.endswith('.c'):
            return 'c'
        elif filename.endswith('.java'):
            return 'java'
        elif filename.endswith('.js'):
            return 'javascript'
        elif filename.endswith('.ts'):
            return 'typescript'
        elif filename.endswith('.go'):
            return 'go'
        elif filename.endswith('.rs'):
            return 'rust'
        elif filename.endswith('.rb'):
            return 'ruby'
        else:
            return 'python'  # Default to Python
    
    async def _execute_compiled_language(self, code: str, language: str, files: dict, input_data: str):
        """Execute code in compiled languages (C++, Java, etc.)"""
        # For now, we'll focus on Python. Compiled language support can be added later
        # by creating appropriate Docker images with compilers
        # Suppress unused parameter warnings by referencing them
        _ = code, files, input_data
        
        from utils.sandboxing import ExecutionResult
        return ExecutionResult(
            success=False,
            output="",
            error=f"Language '{language}' not yet supported. Python is currently supported.",
            execution_time=0.0
        )
    
    async def _format_cp_result(self, result, code: str, language: str, input_data: str, timeout: int):
        """Format competitive programming execution result"""
        # Suppress unused parameter warning
        _ = code
        
        if result.success:
            # Format successful execution
            stats = [
                f"⏱️ **Time:** {result.execution_time:.3f}s / {timeout}s",
                f"💾 **Memory:** {result.memory_used}" if result.memory_used else None,
                f"🔧 **Language:** {language.title()}",
            ]
            stats = [s for s in stats if s]  # Remove None values
            
            if result.files_created:
                stats.append(f"📁 **Files:** {', '.join(result.files_created)}")
            
            # Show input/output clearly for competitive programming
            sections = []
            
            if input_data.strip():
                sections.append(f"**Input:**\n```\n{input_data[:500]}\n```")
            
            output = result.output if result.output else "(no output)"
            if len(output) > 1000:
                output = output[:1000] + "\n... (truncated)"
            sections.append(f"**Output:**\n```\n{output}\n```")
            
            sections.append("\n".join(stats))
            
            return create_embed(
                "✅ Code Execution Successful",
                "\n\n".join(sections),
                color=0x4ECDC4
            )
        else:
            # Format error
            error_msg = result.error if result.error else "Unknown error"
            if len(error_msg) > 1000:
                error_msg = error_msg[:1000] + "\n... (truncated)"
            
            return create_embed(
                "❌ Execution Failed",
                f"**Language:** {language.title()}\n"
                f"⏱️ **Time:** {result.execution_time:.3f}s\n\n"
                f"**Error:**\n```\n{error_msg}\n```",
                color=0xff6b6b
            )


async def setup(bot):
    await bot.add_cog(SystemCog(bot))
