#!/usr/bin/env python3
"""
Diagnose slash command structure for file upload
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from cogs.system import SystemCog
import discord
from discord.ext import commands

def diagnose_eval_command():
    """Check the eval command structure"""
    print("🔍 Diagnosing /eval command structure...")
    
    # Create a dummy bot
    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    # Create the cog
    cog = SystemCog(bot)
    
    # Get the eval command
    eval_cmd = None
    for cmd in cog.get_app_commands():
        if cmd.name == "eval":
            eval_cmd = cmd
            break
    
    if eval_cmd:
        print("✅ Found /eval command")
        print(f"📋 Name: {eval_cmd.name}")
        print(f"📄 Description: {eval_cmd.description}")
        print(f"🔒 Guild Only: {eval_cmd.guild_only}")
        
        print("\n📝 Parameters:")
        for param in eval_cmd.parameters:
            print(f"  - {param.name}")
            print(f"    Type: {param.type}")
            print(f"    Required: {param.required}")
            print(f"    Description: {param.description}")
            print(f"    Default: {param.default}")
            print()
        
        # Check specifically for file parameter
        file_param = None
        for param in eval_cmd.parameters:
            if param.name == "file":
                file_param = param
                break
        
        if file_param:
            print("✅ File parameter found!")
            print(f"🗂️ File parameter type: {file_param.type}")
            print(f"📎 Should show upload button: {file_param.type == discord.Attachment}")
        else:
            print("❌ File parameter NOT found!")
    else:
        print("❌ /eval command not found!")
        print("Available commands:")
        for cmd in cog.get_app_commands():
            print(f"  - {cmd.name}")

if __name__ == "__main__":
    diagnose_eval_command()
