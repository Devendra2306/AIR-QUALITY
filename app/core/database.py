import duckdb
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional
from app.config.settings import settings
from app.config.logging_config import logger


class DatabaseManager:
    """Database connection manager with connection pooling."""
    
    def __init__(self):
        self.db_path = Path(settings.DATABASE_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = None
    
    @contextmanager
    def get_connection(self) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """Get database connection with context manager."""
        conn = duckdb.connect(str(self.db_path))
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: Optional[dict] = None) -> duckdb.DuckDBPyResult:
        """Execute a query and return results."""
        with self.get_connection() as conn:
            if params:
                return conn.execute(query, params)
            return conn.execute(query)
    
    def execute_script(self, script: str) -> None:
        """Execute a SQL script."""
        with self.get_connection() as conn:
            conn.execute(script)
    
    def initialize_schema(self) -> None:
        """Initialize database schema."""
        schema_sql = """
        -- Create schemas
        CREATE SCHEMA IF NOT EXISTS raw;
        CREATE SCHEMA IF NOT EXISTS staging;
        CREATE SCHEMA IF NOT EXISTS presentation;
        CREATE SCHEMA IF NOT EXISTS analytics;
        
        -- Raw measurements table
        CREATE TABLE IF NOT EXISTS raw.measurements (
            id BIGINT PRIMARY KEY,
            location_id BIGINT,
            sensor_id BIGINT,
            location VARCHAR,
            latitude DOUBLE,
            longitude DOUBLE,
            parameter VARCHAR,
            unit VARCHAR,
            value DOUBLE,
            measurement_time TIMESTAMP,
            ingestion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source VARCHAR,
            quality_score DOUBLE
        );
        
        -- Locations table
        CREATE TABLE IF NOT EXISTS staging.locations (
            location_id BIGINT PRIMARY KEY,
            name VARCHAR,
            city VARCHAR,
            country VARCHAR,
            latitude DOUBLE,
            longitude DOUBLE,
            timezone VARCHAR,
            is_active BOOLEAN DEFAULT TRUE,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Sensors table
        CREATE TABLE IF NOT EXISTS staging.sensors (
            sensor_id BIGINT PRIMARY KEY,
            location_id BIGINT,
            name VARCHAR,
            parameter VARCHAR,
            unit VARCHAR,
            is_active BOOLEAN DEFAULT TRUE,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_measurements_location ON raw.measurements(location_id);
        CREATE INDEX IF NOT EXISTS idx_measurements_time ON raw.measurements(measurement_time);
        CREATE INDEX IF NOT EXISTS idx_measurements_parameter ON raw.measurements(parameter);
        """
        self.execute_script(schema_sql)
        logger.info("Database schema initialized")
    
    def get_table_count(self, table_name: str) -> int:
        """Get row count for a table."""
        result = self.execute_query(f"SELECT COUNT(*) FROM {table_name}")
        return result.fetchone()[0]


# Global database manager instance
db_manager = DatabaseManager()
