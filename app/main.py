"""
Air Quality Monitoring System - Main Entry Point

This is the main entry point for the application.
It can run the dashboard, API server, or pipeline orchestrator based on command-line arguments.
"""

import argparse
import sys
from pathlib import Path
from app.config.settings import settings
from app.config.logging_config import logger
from dashboard.app import app as dash_app
from app.pipeline.orchestrator import PipelineOrchestrator


def run_dashboard():
    """Run the dashboard application."""
    logger.info("Starting dashboard application")
    dash_app.run(
        host=settings.HOST,
        port=settings.PORT,
        debug=settings.DEBUG
    )


def run_pipeline():
    """Run the data pipeline."""
    logger.info("Starting data pipeline")
    
    orchestrator = PipelineOrchestrator()
    
    # Run pipeline with default settings
    results = orchestrator.run_pipeline(
        sync_locations=True,
        collect_latest=True
    )
    
    logger.info(f"Pipeline completed: {results}")
    return results


def run_location_sync():
    """Sync locations from OpenAQ."""
    logger.info("Starting location sync")
    
    orchestrator = PipelineOrchestrator()
    results = orchestrator.run_location_sync(limit=1000)
    
    logger.info(f"Location sync completed: {results}")
    return results


def run_measurement_collection(location_ids: list = None):
    """Collect measurements for specified locations."""
    logger.info("Starting measurement collection")
    
    orchestrator = PipelineOrchestrator()
    
    if not location_ids:
        # Get all active locations from database
        from app.core.database import db_manager
        query = "SELECT location_id FROM staging.locations WHERE is_active = TRUE"
        with db_manager.get_connection() as conn:
            result = conn.execute(query)
            location_ids = [row[0] for row in result.fetchall()]
    
    results = orchestrator.run_measurement_collection(
        location_ids=location_ids,
        collect_latest=True
    )
    
    logger.info(f"Measurement collection completed: {results}")
    return results


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Air Quality Monitoring System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app/main.py dashboard              # Run the dashboard
  python app/main.py pipeline               # Run the full pipeline
  python app/main.py sync-locations         # Sync locations only
  python app/main.py collect-measurements   # Collect measurements only
        """
    )
    
    parser.add_argument(
        "command",
        choices=["dashboard", "pipeline", "sync-locations", "collect-measurements"],
        help="Command to run"
    )
    
    parser.add_argument(
        "--location-ids",
        nargs="+",
        type=int,
        help="Specific location IDs for measurement collection"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    # Override debug setting if specified
    if args.debug:
        settings.DEBUG = True
        logger.info("Debug mode enabled")
    
    # Execute command
    try:
        if args.command == "dashboard":
            run_dashboard()
        elif args.command == "pipeline":
            run_pipeline()
        elif args.command == "sync-locations":
            run_location_sync()
        elif args.command == "collect-measurements":
            run_measurement_collection(args.location_ids)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
