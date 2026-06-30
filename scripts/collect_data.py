"""
Data Collection Script

Collects latest measurements from OpenAQ for all active locations.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pipeline.orchestrator import PipelineOrchestrator
from app.core.database import db_manager
from app.config.logging_config import logger


def main():
    """Collect latest measurements."""
    logger.info("Starting data collection")
    
    try:
        # Get all active locations
        query = "SELECT location_id FROM staging.locations WHERE is_active = TRUE LIMIT 50"
        with db_manager.get_connection() as conn:
            result = conn.execute(query)
            location_ids = [row[0] for row in result.fetchall()]
        
        if not location_ids:
            logger.warning("No active locations found")
            print("✗ No active locations found. Run seed_locations.py first.")
            sys.exit(1)
        
        logger.info(f"Collecting data for {len(location_ids)} locations")
        
        orchestrator = PipelineOrchestrator()
        results = orchestrator.run_measurement_collection(
            location_ids=location_ids,
            collect_latest=True
        )
        
        logger.info(f"Data collection completed: {results}")
        print(f"✓ Collected {results.get('loaded', 0)} measurements")
    except Exception as e:
        logger.error(f"Data collection failed: {str(e)}")
        print(f"✗ Data collection failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
