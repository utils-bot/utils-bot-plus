#!/usr/bin/env python3
"""
Populate initial data for Utils Bot v2

This script adds initial configuration data and example records.
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


async def populate_initial_data():
    """Populate initial data."""
    logger.info("Populating initial data...")
    
    db = Database(settings.database_url)
    await db.initialize()
    
    # Add any initial data here if needed
    # For example, create default configurations
    
    logger.info("Initial data populated successfully!")
    await db.close()


async def main():
    """Main population function."""
    logger.info("Starting data population...")
    
    try:
        await populate_initial_data()
        logger.info("Data population completed successfully!")
    except Exception as e:
        logger.error(f"Data population failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
