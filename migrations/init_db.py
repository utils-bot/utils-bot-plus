#!/usr/bin/env python3
"""
Database migration script for Utils Bot v2

This script creates the initial database schema and populates initial data.
Run this before starting the bot for the first time.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import Database
from config.settings import settings
from core.logger import get_logger

logger = get_logger(__name__)


async def create_initial_schema():
    """Create the initial database schema."""
    logger.info("Creating initial database schema...")
    
    db = Database(settings.database_url)
    await db.initialize()
    
    logger.info("Database schema created successfully!")
    await db.close()


async def main():
    """Main migration function."""
    logger.info("Starting database migration...")
    
    try:
        await create_initial_schema()
        logger.info("Migration completed successfully!")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
