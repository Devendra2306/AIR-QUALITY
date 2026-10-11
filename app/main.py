"""
Air Quality Monitoring System - Main Entry Point

This is the main entry point for the application.
It can run the dashboard, API server, or pipeline orchestrator based on command-line arguments.
"""

import argparse
import sys
from pathlib import Path

# Add project root to Python search path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config.settings import settings
from app.config.logging_config import logger
from app.pipeline.orchestrator import PipelineOrchestrator


def run_dashboard():
    """Run the dashboard application."""
    logger.info("Starting dashboard application")
    from app.dashboard.app import app as dash_app
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


def run_model_training():
    """Run model training."""
    from scripts.train_model import main as train_main
    train_main()


def run_data_generation():
    """Generate realistic sample dataset."""
    from scripts.generate_sample_dataset import generate_dataset, seed_database_from_dataframe
    df = generate_dataset()
    seed_database_from_dataframe(df)


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Air Quality Monitoring System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app/main.py                        # Default: Run the dashboard
  python app/main.py dashboard              # Run the interactive dashboard
  python app/main.py train-model            # Train Machine Learning model
  python app/main.py generate-data          # Generate multi-city sample dataset
  python app/main.py pipeline               # Run the ETL pipeline
        """
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        default="dashboard",
        choices=["dashboard", "pipeline", "sync-locations", "collect-measurements", "train-model", "generate-data"],
        help="Command to run (default: dashboard)"
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
        elif args.command == "train-model":
            run_model_training()
        elif args.command == "generate-data":
            run_data_generation()
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
