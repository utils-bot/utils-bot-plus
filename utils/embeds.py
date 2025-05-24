"""
Discord embed utilities for Utils Bot v2.0
"""

from typing import Optional, Union
import discord
from config.settings import assets


def create_embed(
    title: str,
    description: Optional[str] = None,
    color: Union[int, discord.Color] = assets.PRIMARY_COLOR,
    thumbnail: Optional[str] = None,
    image: Optional[str] = None,
    footer: Optional[str] = None,
    footer_icon: Optional[str] = None,
    author: Optional[str] = None,
    author_icon: Optional[str] = None,
    url: Optional[str] = None
) -> discord.Embed:
    """
    Create a standardized embed
    
    Args:
        title: Embed title
        description: Embed description
        color: Embed color (default: primary blue)
        thumbnail: Thumbnail URL
        image: Image URL
        footer: Footer text
        footer_icon: Footer icon URL
        author: Author name
        author_icon: Author icon URL
        url: Embed URL
        
    Returns:
        Configured Discord embed
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        url=url
    )
    
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    
    if image:
        embed.set_image(url=image)
    
    if footer:
        embed.set_footer(text=footer, icon_url=footer_icon)
    
    if author:
        embed.set_author(name=author, icon_url=author_icon)
    
    return embed


def create_success_embed(
    title: str,
    description: Optional[str] = None,
    **kwargs
) -> discord.Embed:
    """Create a success-themed embed"""
    return create_embed(
        title=f"✅ {title}",
        description=description,
        color=assets.SUCCESS_COLOR,
        **kwargs
    )


def create_error_embed(
    title: str,
    description: Optional[str] = None,
    **kwargs
) -> discord.Embed:
    """Create an error-themed embed"""
    return create_embed(
        title=f"❌ {title}",
        description=description,
        color=assets.ERROR_COLOR,
        **kwargs
    )


def create_warning_embed(
    title: str,
    description: Optional[str] = None,
    **kwargs
) -> discord.Embed:
    """Create a warning-themed embed"""
    return create_embed(
        title=f"⚠️ {title}",
        description=description,
        color=assets.WARNING_COLOR,
        **kwargs
    )


def create_info_embed(
    title: str,
    description: Optional[str] = None,
    **kwargs
) -> discord.Embed:
    """Create an info-themed embed"""
    return create_embed(
        title=f"ℹ️ {title}",
        description=description,
        color=assets.INFO_COLOR,
        **kwargs
    )


def create_loading_embed(
    title: str = "Processing...",
    description: Optional[str] = None
) -> discord.Embed:
    """Create a loading embed"""
    return create_embed(
        title=f"⏳ {title}",
        description=description,
        color=assets.INFO_COLOR
    )


class PaginatedEmbed:
    """
    Helper class for creating paginated embeds
    """
    
    def __init__(
        self,
        pages: list,
        title: str,
        color: Union[int, discord.Color] = assets.PRIMARY_COLOR,
        per_page: int = 10
    ):
        self.pages = pages
        self.title = title
        self.color = color
        self.per_page = per_page
        self.current_page = 0
        self.total_pages = (len(pages) + per_page - 1) // per_page
    
    def get_embed(self, page: int = 0) -> discord.Embed:
        """Get embed for specific page"""
        if page < 0 or page >= self.total_pages:
            page = 0
        
        self.current_page = page
        start_idx = page * self.per_page
        end_idx = start_idx + self.per_page
        page_items = self.pages[start_idx:end_idx]
        
        embed = create_embed(
            title=self.title,
            description="\n".join(str(item) for item in page_items),
            color=self.color,
            footer=f"Page {page + 1}/{self.total_pages}"
        )
        
        return embed
    
    def has_previous(self) -> bool:
        """Check if there's a previous page"""
        return self.current_page > 0
    
    def has_next(self) -> bool:
        """Check if there's a next page"""
        return self.current_page < self.total_pages - 1


def format_user(user: Union[discord.User, discord.Member]) -> str:
    """Format user for display in embeds"""
    return f"{user.mention} ({user.display_name})"


def format_timestamp(timestamp: Union[int, float]) -> str:
    """Format timestamp for Discord"""
    return f"<t:{int(timestamp)}:R>"


def format_duration(seconds: float) -> str:
    """Format duration in a readable way"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"
