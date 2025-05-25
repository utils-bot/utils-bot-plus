#!/usr/bin/env python3
"""
Manual command sync script to ensure slash commands are properly registered
"""

import asyncio
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

async def sync_commands():
    """Manually sync slash commands to Discord"""
    
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("❌ BOT_TOKEN not found in environment variables")
        return
    
    dev_guild_id = os.getenv("DEV_GUILD_ID")
    
    intents = discord.Intents.default()
    intents.message_content = True
    
    bot = commands.Bot(
        command_prefix="$disabled$",
        intents=intents,
        help_command=None
    )
    
    @bot.event
    async def on_ready():
        print(f"🤖 Bot logged in as {bot.user}")
        
        try:
            # Load the system cog to register commands
            await bot.load_extension("cogs.system")
            print("✅ Loaded system cog")
            
            # Sync globally
            print("🌍 Syncing global commands...")
            synced_global = await bot.tree.sync()
            print(f"✅ Synced {len(synced_global)} global commands")
            
            # Print command details
            for cmd in synced_global:
                print(f"  📋 {cmd.name}: {cmd.description}")
                if hasattr(cmd, 'options') and cmd.options:
                    for option in cmd.options:
                        print(f"    - {option.name} ({option.type.name}): {option.description}")
            
            # Sync to dev guild if specified
            if dev_guild_id and dev_guild_id != "0":
                print(f"🏠 Syncing to dev guild {dev_guild_id}...")
                guild = discord.Object(id=int(dev_guild_id))
                synced_dev = await bot.tree.sync(guild=guild)
                print(f"✅ Synced {len(synced_dev)} commands to dev guild")
                
                for cmd in synced_dev:
                    print(f"  📋 {cmd.name}: {cmd.description}")
                    if hasattr(cmd, 'options') and cmd.options:
                        for option in cmd.options:
                            print(f"    - {option.name} ({option.type.name}): {option.description}")
            
            print("\n🎉 Command sync completed!")
            print("💡 Try using /eval in Discord - you should see the file upload button")
            print("⚠️  Note: It may take a few minutes for Discord to update the command interface")
            
        except Exception as e:
            print(f"❌ Error during sync: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await bot.close()
            # Give time for cleanup
            await asyncio.sleep(1)
    
    await bot.start(bot_token)

if __name__ == "__main__":
    asyncio.run(sync_commands())
