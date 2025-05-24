"""
Database models and management for Utils Bot v2.0
"""

from pathlib import Path
from typing import List, Optional

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

from core.logger import get_logger

Base = declarative_base()
logger = get_logger(__name__)


class User(Base):
    """User model for storing user data"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    discord_id = Column(String(20), unique=True, nullable=False)
    username = Column(String(100), nullable=False)
    is_whitelisted = Column(Boolean, default=False)
    is_blacklisted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Guild(Base):
    """Guild model for storing server data"""
    __tablename__ = "guilds"
    
    id = Column(Integer, primary_key=True)
    discord_id = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    prefix = Column(String(10), default="!")
    is_blacklisted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class GameStats(Base):
    """Game statistics model"""
    __tablename__ = "game_stats"
    
    id = Column(Integer, primary_key=True)
    user_discord_id = Column(String(20), nullable=False)
    game_type = Column(String(50), nullable=False)  # wordle, etc.
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    best_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class APIUsage(Base):
    """API usage tracking model"""
    __tablename__ = "api_usage"
    
    id = Column(Integer, primary_key=True)
    user_discord_id = Column(String(20), nullable=False)
    api_name = Column(String(50), nullable=False)  # gemini, screenshot, etc.
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())


class Database:
    """Database manager class"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.async_session = None
        
    async def initialize(self) -> None:
        """Initialize the database connection and create tables"""
        try:
            # Create data directory if using SQLite
            if self.database_url.startswith("sqlite"):
                db_path = Path(self.database_url.replace("sqlite:///", ""))
                db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create async engine
            self.engine = create_async_engine(
                self.database_url,
                echo=False,  # Set to True for SQL debugging
                future=True
            )
            
            # Create session maker
            self.async_session = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close(self) -> None:
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")
    
    async def get_user(self, discord_id: int) -> Optional[User]:
        """Get user by Discord ID"""
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.discord_id == str(discord_id))
            )
            return result.scalar_one_or_none()
    
    async def create_user(self, discord_id: int, username: str) -> User:
        """Create a new user"""
        async with self.async_session() as session:
            user = User(discord_id=str(discord_id), username=username)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
    
    async def get_or_create_user(self, discord_id: int, username: str) -> User:
        """Get existing user or create new one"""
        user = await self.get_user(discord_id)
        if not user:
            user = await self.create_user(discord_id, username)
        return user
    
    async def update_user_whitelist(self, discord_id: int, is_whitelisted: bool) -> bool:
        """Update user whitelist status"""
        async with self.async_session() as session:
            from sqlalchemy import select, update
            user = await session.execute(
                select(User).where(User.discord_id == str(discord_id))
            )
            user_obj = user.scalar_one_or_none()
            if user_obj:
                await session.execute(
                    update(User)
                    .where(User.discord_id == str(discord_id))
                    .values(is_whitelisted=is_whitelisted)
                )
                await session.commit()
                return True
            return False
    
    async def get_whitelisted_users(self) -> List[int]:
        """Get list of whitelisted user IDs"""
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(User.discord_id).where(User.is_whitelisted == True)
            )
            return [int(row[0]) for row in result.fetchall()]
    
    async def get_guild(self, discord_id: int) -> Optional[Guild]:
        """Get guild by Discord ID"""
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Guild).where(Guild.discord_id == str(discord_id))
            )
            return result.scalar_one_or_none()
    
    async def create_guild(self, discord_id: int, name: str) -> Guild:
        """Create a new guild"""
        async with self.async_session() as session:
            guild = Guild(discord_id=str(discord_id), name=name)
            session.add(guild)
            await session.commit()
            await session.refresh(guild)
            return guild
    
    async def get_or_create_guild(self, discord_id: int, name: str) -> Guild:
        """Get existing guild or create new one"""
        guild = await self.get_guild(discord_id)
        if not guild:
            guild = await self.create_guild(discord_id, name)
        return guild
    
    async def track_api_usage(self, user_discord_id: int, api_name: str) -> None:
        """Track API usage for a user"""
        async with self.async_session() as session:
            from sqlalchemy import select, update
            
            # Check if record exists
            result = await session.execute(
                select(APIUsage).where(
                    APIUsage.user_discord_id == str(user_discord_id),
                    APIUsage.api_name == api_name
                )
            )
            usage = result.scalar_one_or_none()
            
            if usage:
                await session.execute(
                    update(APIUsage)
                    .where(
                        APIUsage.user_discord_id == str(user_discord_id),
                        APIUsage.api_name == api_name
                    )
                    .values(
                        usage_count=APIUsage.usage_count + 1,
                        last_used=datetime.now()
                    )
                )
            else:
                usage = APIUsage(
                    user_discord_id=str(user_discord_id),
                    api_name=api_name,
                    usage_count=1
                )
                session.add(usage)
            
            await session.commit()
    
    async def get_game_stats(self, user_discord_id: int, game_type: str) -> Optional[GameStats]:
        """Get game statistics for a user"""
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(GameStats).where(
                    GameStats.user_discord_id == str(user_discord_id),
                    GameStats.game_type == game_type
                )
            )
            return result.scalar_one_or_none()
    
    async def update_game_stats(self, user_discord_id: int, game_type: str, won: bool, score: int = 0) -> None:
        """Update game statistics for a user"""
        async with self.async_session() as session:
            from sqlalchemy import select, update
            
            # Check if stats exist
            result = await session.execute(
                select(GameStats).where(
                    GameStats.user_discord_id == str(user_discord_id),
                    GameStats.game_type == game_type
                )
            )
            stats = result.scalar_one_or_none()
            
            if not stats:
                stats = GameStats(
                    user_discord_id=str(user_discord_id),
                    game_type=game_type,
                    games_played=1,
                    games_won=1 if won else 0,
                    best_score=score if won else 0
                )
                session.add(stats)
            else:
                # Use update statement for existing records
                update_values = {
                    "games_played": GameStats.games_played + 1
                }
                if won:
                    update_values["games_won"] = GameStats.games_won + 1
                    # Only update best score if this score is better
                    if score > 0:
                        current_best = await session.execute(
                            select(GameStats.best_score).where(
                                GameStats.user_discord_id == str(user_discord_id),
                                GameStats.game_type == game_type
                            )
                        )
                        current_best_value = current_best.scalar()
                        if current_best_value is None or score > current_best_value:
                            update_values["best_score"] = score
                
                await session.execute(
                    update(GameStats)
                    .where(
                        GameStats.user_discord_id == str(user_discord_id),
                        GameStats.game_type == game_type
                    )
                    .values(**update_values)
                )
            
            await session.commit()
