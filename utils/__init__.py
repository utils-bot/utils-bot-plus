"""
Utilities package for Utils Bot v2.0
"""

from .checks import is_developer, is_whitelisted, dev_only, requires_whitelist, guild_only, cooldown
from .embeds import (
    create_embed, create_success_embed, create_error_embed, 
    create_warning_embed, create_info_embed, create_loading_embed,
    PaginatedEmbed, format_user, format_timestamp, format_duration
)

__all__ = [
    # Checks
    "is_developer", "is_whitelisted", "dev_only", "requires_whitelist", 
    "guild_only", "cooldown",
    # Embeds
    "create_embed", "create_success_embed", "create_error_embed",
    "create_warning_embed", "create_info_embed", "create_loading_embed",
    "PaginatedEmbed", "format_user", "format_timestamp", "format_duration"
]
