"""
Permission checks and decorators for Utils Bot v2.0
"""

from typing import Callable, Any
from functools import wraps

import discord
from discord.ext import commands

from config.settings import settings
from core.logger import get_logger

logger = get_logger(__name__)


def is_developer(user_id: int) -> bool:
    """Check if user is a developer"""
    return user_id in settings.dev_ids


def is_owner() -> Callable:
    """Decorator to check if user is bot owner"""
    def predicate(interaction: discord.Interaction) -> bool:
        return is_developer(interaction.user.id)
    
    return discord.app_commands.check(predicate)


async def is_whitelisted(user_id: int, bot) -> bool:
    """Check if user is whitelisted for beta features"""
    if not settings.closed_beta:
        return True
    
    if is_developer(user_id):
        return True
    
    if bot.db:
        user = await bot.db.get_user(user_id)
        return user and user.is_whitelisted
    
    return False


def requires_whitelist() -> Callable:
    """Decorator to check if user is whitelisted"""
    async def predicate(interaction: discord.Interaction) -> bool:
        if not settings.closed_beta:
            return True
        
        if is_developer(interaction.user.id):
            return True
        
        bot = interaction.client
        if bot.db:
            user = await bot.db.get_user(interaction.user.id)
            return user and user.is_whitelisted
        
        return False
    
    return discord.app_commands.check(predicate)


def dev_only() -> Callable:
    """Decorator for developer-only commands"""
    def predicate(interaction: discord.Interaction) -> bool:
        return is_developer(interaction.user.id)
    
    return discord.app_commands.check(predicate)


def guild_only() -> Callable:
    """Decorator to ensure command is used in a guild"""
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.guild is not None
    
    return discord.app_commands.check(predicate)


class CooldownByUser(discord.app_commands.Cooldown):
    """Per-user cooldown that exempts developers"""
    
    def __init__(self, rate: int, per: float):
        super().__init__(rate, per)
    
    def __call__(self, interaction: discord.Interaction) -> bool:
        # Developers are exempt from cooldowns
        if is_developer(interaction.user.id):
            return False
        
        return super().__call__(interaction)


def cooldown(rate: int, per: float) -> Callable:
    """Apply cooldown with developer exemption"""
    def decorator(func):
        # Add cooldown with developer exemption
        cooldown_instance = CooldownByUser(rate, per)
        return discord.app_commands.checks.cooldown(rate, per)(func)
    return decorator
