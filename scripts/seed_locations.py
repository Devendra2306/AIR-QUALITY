"""
Location Seeding Script

Fetches and seeds locations from OpenAQ API into the database.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pipeline.orchestrator import PipelineOrchestrator
from app.config.logging_config import logger


def main():
    """Seed locations from OpenAQ."""
    logger.info("Starting location seeding")
    
    try:
        orchestrator = PipelineOrchestrator()
        
        # Sync locations (default: all countries, limit 1000)
        results = orchestrator.run_location_sync(limit=1000)
        
        logger.info(f"Location seeding completed: {results}")
        print(f"✓ Seeded {results.get('loaded', 0)} locations")
    except Exception as e:
        logger.error(f"Location seeding failed: {str(e)}")
        print(f"✗ Location seeding failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
