from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.pipeline.extractors.openaq_extractor import OpenAQExtractor
from app.pipeline.transformers.quality_transformer import QualityTransformer
from app.pipeline.loaders.database_loader import DatabaseLoader
from app.core.database import db_manager
from app.config.settings import settings
from app.config.logging_config import logger


class PipelineOrchestrator:
    """Orchestrate the ETL pipeline with error handling and monitoring."""
    
    def __init__(self):
        self.extractor = OpenAQExtractor()
        self.transformer = QualityTransformer()
        self.loader = DatabaseLoader(batch_size=1000)
        self.pipeline_stats = {
            "extracted": 0,
            "transformed": 0,
            "loaded": 0,
            "errors": 0,
            "start_time": None,

            "end_time": None
        }
    
    def run_location_sync(
        self,
        country: Optional[str] = None,
        city: Optional[str] = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """Sync locations from OpenAQ."""
        logger.info(f"Starting location sync for country={country}, city={city}")
        self.pipeline_stats["start_time"] = datetime.now()
        
        try:
            # Extract
            raw_locations = self.extractor.extract(
                type="locations",
                country=country,
                city=city,
                limit=limit
            )
            self.pipeline_stats["extracted"] = len(raw_locations)
            
            # Validate
            if not self.extractor.validate_data(raw_locations):
                raise ValueError("Location data validation failed")
            
            # Load
            loaded = self.loader.load_locations(raw_locations)
            self.pipeline_stats["loaded"] = loaded
            
            self.pipeline_stats["end_time"] = datetime.now()
            logger.info(f"Location sync completed: {loaded} locations loaded")
            
            return self.pipeline_stats
            
        except Exception as e:
            self.pipeline_stats["errors"] += 1
            logger.error(f"Location sync failed: {str(e)}")
            raise
    
    def run_measurement_collection(
        self,
        location_ids: List[int],
        collect_latest: bool = True
    ) -> Dict[str, Any]:
        """Collect measurements for specified locations."""
        logger.info(f"Starting measurement collection for {len(location_ids)} locations")
        self.pipeline_stats["start_time"] = datetime.now()
        
        all_measurements = []
        
        for location_id in location_ids:
            try:
                if collect_latest:
                    raw_data = self.extractor.extract(
                        type="latest",
                        location_id=location_id,
                        limit=100
                    )
                else:
                    # Collect last 24 hours
                    date_from = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                    date_to = datetime.now().strftime("%Y-%m-%d")
                    raw_data = self.extractor.extract(
                        type="measurements",
                        location_id=location_id,
                        date_from=date_from,
                        date_to=date_to,
                        limit=1000
                    )
                
                all_measurements.extend(raw_data)
                self.pipeline_stats["extracted"] += len(raw_data)
                
            except Exception as e:
                self.pipeline_stats["errors"] += 1
                logger.error(f"Failed to collect measurements for location {location_id}: {str(e)}")
                continue
        
        # Transform
        if all_measurements:
            transformed_data = self.transformer.transform_measurements(all_measurements)
            self.pipeline_stats["transformed"] = len(transformed_data)
            
            # Load
            loaded = self.loader.load_measurements(transformed_data)
            self.pipeline_stats["loaded"] = loaded
        
        self.pipeline_stats["end_time"] = datetime.now()
        logger.info(f"Measurement collection completed: {self.pipeline_stats['loaded']} records loaded")
        
        return self.pipeline_stats
    
    def run_pipeline(
        self,
        sync_locations: bool = False,
        location_ids: Optional[List[int]] = None,
        collect_latest: bool = True
    ) -> Dict[str, Any]:
        """Run complete pipeline."""
        logger.info("Starting pipeline execution")
        
        # Initialize database
        try:
            db_manager.initialize_schema()
        except Exception as e:
            logger.warning(f"Schema initialization warning: {str(e)}")
        
        results = {}
        
        # Sync locations if requested
        if sync_locations:
            results["location_sync"] = self.run_location_sync()
        
        # Collect measurements
        if location_ids:
            results["measurement_collection"] = self.run_measurement_collection(
                location_ids,
                collect_latest
            )
        
        # Create presentation views
        self._create_presentation_views()
        
        logger.info("Pipeline execution completed")
        return results
    
    def _create_presentation_views(self) -> None:
        """Create presentation layer views."""
        views = {
            "presentation.latest_measurements": """
                SELECT DISTINCT ON (location_id, parameter)
                    location_id,
                    location,
                    latitude,
                    longitude,
                    parameter,
                    unit,
                    value,
                    measurement_time,
                    quality_score
                FROM raw.measurements
                WHERE quality_score > 0.5
                ORDER BY location_id, parameter, measurement_time DESC
            """,
            "presentation.daily_aggregates": """
                SELECT
                    location_id,
                    location,
                    parameter,
                    unit,
                    DATE(measurement_time) as measurement_date,
                    AVG(value) as avg_value,
                    MIN(value) as min_value,
                    MAX(value) as max_value,
                    STDDEV(value) as std_value,
                    COUNT(*) as measurement_count,
                    AVG(quality_score) as avg_quality
                FROM raw.measurements
                WHERE quality_score > 0.5
                GROUP BY
                    location_id,
                    location,
                    parameter,
                    unit,
                    DATE(measurement_time)
                ORDER BY measurement_date DESC, location_id
            """,
            "presentation.location_summary": """
                SELECT
                    l.location_id,
                    l.name as location_name,
                    l.city,
                    l.country,
                    l.latitude,
                    l.longitude,
                    COUNT(DISTINCT m.parameter) as parameter_count,
                    MAX(m.measurement_time) as last_measurement_time,
                    AVG(m.quality_score) as avg_quality_score
                FROM staging.locations l
                LEFT JOIN raw.measurements m ON l.location_id = m.location_id
                WHERE l.is_active = TRUE
                GROUP BY l.location_id, l.name, l.city, l.country, l.latitude, l.longitude
            """
        }
        
        for view_name, query in views.items():
            try:
                self.loader.create_materialized_view(view_name, query)
            except Exception as e:
                logger.error(f"Failed to create view {view_name}: {str(e)}")
