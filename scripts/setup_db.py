"""
Database Setup Script

Initializes the database schema and creates necessary tables.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import db_manager
from app.config.logging_config import logger


def main():
    """Setup database schema."""
    logger.info("Starting database setup")
    
    try:
        db_manager.initialize_schema()
        logger.info("Database setup completed successfully")
        print("✓ Database initialized successfully")
    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        print(f"✗ Database setup failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
