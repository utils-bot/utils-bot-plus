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
        
        # Define command categories with emojis
        command_categories = {
            "Information": {"emoji": "ℹ️", "commands": []},
            "AI": {"emoji": "🤖", "commands": []},
            "Games": {"emoji": "🎮", "commands": []},
            "Tools": {"emoji": "🔧", "commands": []},
            "Network": {"emoji": "🌐", "commands": []},
            "System": {"emoji": "⚙️", "commands": []}
        }
        
        # Categorize commands
        for cmd in all_commands:
            if hasattr(cmd, 'binding') and cmd.binding:
                cog_name = getattr(cmd.binding, 'qualified_name', 'Other')
                
                # Map cog names to user-friendly categories
                if cog_name == "Info":
                    command_categories["Information"]["commands"].append(cmd)
                elif cog_name == "AI":
                    command_categories["AI"]["commands"].append(cmd)
                elif cog_name == "Games":
                    command_categories["Games"]["commands"].append(cmd)
                elif cog_name == "Tools":
                    command_categories["Tools"]["commands"].append(cmd)
                elif cog_name == "Network":
                    command_categories["Network"]["commands"].append(cmd)
                elif cog_name == "System":
                    command_categories["System"]["commands"].append(cmd)

        # Filter by category if specified
        if category:
            if category not in command_categories:
                embed = create_error_embed(
                    "Invalid Category",
                    f"Category '{category}' not found.\n\n"
                    f"Available categories: {', '.join(command_categories.keys())}"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Show only the specified category
            filtered_categories = {category: command_categories[category]}
            command_categories = filtered_categories

        # Create help embed
        embed = create_embed(
            "🛠️ UtilsBot+ Commands",
            f"Here are all available slash commands{f' in the **{category}** category' if category else ''}.\n"
            f"📖 **[Complete User Guide](https://github.com/ad1107/utils-bot-plus/wiki/3.-For-Users)**",
            thumbnail=self.bot.user.display_avatar.url if self.bot.user else None
        )
        
        # Add fields for each category
        total_commands = 0
        for cat_name, cat_data in command_categories.items():
            commands = cat_data["commands"]
            emoji = cat_data["emoji"]
            
            if not commands:
                continue
                
            # Create command list for this category
            command_list = []
            for cmd in commands:
                # Handle both regular commands and groups
                if hasattr(cmd, 'commands') and cmd.commands:  # This is a group
                    # Add the group and its subcommands
                    command_list.append(f"**`/{cmd.name}`** - {cmd.description}")
                    for subcmd in cmd.commands:
                        command_list.append(f"  └ `/{cmd.name} {subcmd.name}` - {subcmd.description}")
                        total_commands += 1
                else:  # Regular command
                    # Add dev-only marker for system commands
                    dev_marker = " 🔒" if cat_name == "System" else ""
                    command_list.append(f"`/{cmd.name}` - {cmd.description}{dev_marker}")
                    total_commands += 1
            
            if command_list:
                # Split long command lists into multiple fields if needed
                command_text = "\n".join(command_list)
                if len(command_text) > 1024:
                    # Split into chunks of ~800 characters to be safe
                    chunks = []
                    current_chunk = []
                    current_length = 0
                    
                    for cmd_line in command_list:
                        if current_length + len(cmd_line) + 1 > 800:
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
                        field_name = f"{emoji} {cat_name}" if i == 0 else f"{emoji} {cat_name} (cont.)"
                        embed.add_field(name=field_name, value=chunk, inline=False)
                else:
                    embed.add_field(name=f"{emoji} {cat_name}", value=command_text, inline=False)

        # Add usage information
        if not category:
            embed.add_field(
                name="💡 How to Use Commands",
                value=(
                    "• Type `/` and Discord will show available commands\n"
                    "• Use `/help <category>` to filter by category\n"
                    "• Commands with 🔒 require developer permissions\n"
                    "• Use `ephemeral:true` on sensitive commands for privacy\n"
                    "• Visit our **[User Guide](https://github.com/ad1107/utils-bot-plus/wiki/3.-For-Users)** for detailed examples!"
                ),
                inline=False
            )

        # Add footer with command count and links
        footer_text = f"Total commands: {total_commands}"
        if not category:
            footer_text += " | Use /help <category> to filter"
        
        embed.set_footer(text=footer_text)
        
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
