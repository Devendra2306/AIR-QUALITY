from typing import List, Dict, Any, Optional
from app.core.database import db_manager
from app.config.logging_config import logger


class DatabaseLoader:
    """Load transformed data into database with batch processing."""
    
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
    
    def load_measurements(
        self,
        data: List[Dict[str, Any]],
        table: str = "raw.measurements"
    ) -> int:
        """Load measurement data into database."""
        if not data:
            logger.warning("No data to load")
            return 0
        
        loaded_count = 0
        
        # Process in batches
        for i in range(0, len(data), self.batch_size):
            batch = data[i:i + self.batch_size]
            
            # Prepare insert statement
            columns = list(batch[0].keys())
            placeholders = ", ".join(["?"] * len(columns))
            columns_str = ", ".join(columns)
            
            insert_sql = f"""
            INSERT INTO {table} ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
            """
            
            # Prepare values
            values = []
            for record in batch:
                values.append([record.get(col) for col in columns])
            
            try:
                with db_manager.get_connection() as conn:
                    conn.executemany(insert_sql, values)
                    loaded_count += len(batch)
                    logger.info(f"Loaded batch {i//self.batch_size + 1}: {len(batch)} records")
            except Exception as e:
                logger.error(f"Error loading batch: {str(e)}")
                raise
        
        logger.info(f"Total loaded: {loaded_count} records")
        return loaded_count
    
    def load_locations(
        self,
        data: List[Dict[str, Any]],
        table: str = "staging.locations"
    ) -> int:
        """Load location data into database."""
        if not data:
            return 0
        
        # Transform location data
        transformed_data = []
        for item in data:
            transformed_data.append({
                "location_id": item.get("id"),
                "name": item.get("name"),
                "city": item.get("city"),
                "country": item.get("country"),
                "latitude": item.get("coordinates", {}).get("latitude") if isinstance(item.get("coordinates"), dict) else None,
                "longitude": item.get("coordinates", {}).get("longitude") if isinstance(item.get("coordinates"), dict) else None,
                "timezone": item.get("timezone"),
                "is_active": True,
                "last_updated": None  # Will use default
            })
        
        return self.load_measurements(transformed_data, table)
    
    def upsert_location(
        self,
        location_data: Dict[str, Any]
    ) -> bool:
        """Upsert a single location record."""
        sql = """
        INSERT INTO staging.locations (
            location_id, name, city, country, latitude, longitude, timezone, is_active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (location_id) DO UPDATE SET
            name = EXCLUDED.name,
            city = EXCLUDED.city,
            country = EXCLUDED.country,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            timezone = EXCLUDED.timezone,
            is_active = EXCLUDED.is_active,
            last_updated = CURRENT_TIMESTAMP
        """
        
        try:
            with db_manager.get_connection() as conn:
                conn.execute(sql, [
                    location_data.get("location_id"),
                    location_data.get("name"),
                    location_data.get("city"),
                    location_data.get("country"),
                    location_data.get("latitude"),
                    location_data.get("longitude"),
                    location_data.get("timezone"),
                    location_data.get("is_active", True)
                ])
            logger.info(f"Upserted location {location_data.get('location_id')}")
            return True
        except Exception as e:
            logger.error(f"Error upserting location: {str(e)}")
            return False
    
    def create_materialized_view(
        self,
        view_name: str,
        query: str
    ) -> None:
        """Create or replace a materialized view."""
        sql = f"CREATE OR REPLACE VIEW {view_name} AS {query}"
        
        try:
            db_manager.execute_script(sql)
            logger.info(f"Created materialized view: {view_name}")
        except Exception as e:
            logger.error(f"Error creating view {view_name}: {str(e)}")
            raise
    
    def refresh_materialized_view(self, view_name: str) -> None:
        """Refresh a materialized view."""
        # DuckDB doesn't have REFRESH MATERIALIZED VIEW like PostgreSQL
        # Views are automatically refreshed when queried
        logger.info(f"View {view_name} will be refreshed on next query")
