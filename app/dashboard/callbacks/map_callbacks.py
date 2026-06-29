from dash import Input, Output, State
from app.core.database import db_manager
from app.dashboard.components.charts import create_map_figure
from app.config.logging_config import logger
import pandas as pd


def register_map_callbacks(app):
    """Register map-related callbacks."""
    
    @app.callback(
        Output("map-view", "figure"),
        Input("refresh-interval", "n_intervals"),
        Input("location-filter", "value"),
        Input("parameter-filter", "value")
    )
    def update_map(n_intervals, location_filter, parameter_filter):
        """Update the map view with latest data."""
        try:
            # Build query
            query = """
            SELECT 
                location_id,
                location,
                latitude,
                longitude,
                parameter,
                value,
                measurement_time
            FROM presentation.latest_measurements
            WHERE quality_score > 0.5
            """
            
            params = {}
            
            if location_filter:
                query += " AND location_id = $location_id"
                params["location_id"] = location_filter
            
            if parameter_filter:
                query += " AND parameter = $parameter"
                params["parameter"] = parameter_filter
            
            query += " ORDER BY measurement_time DESC"
            
            # Execute query
            with db_manager.get_connection() as conn:
                if params:
                    result = conn.execute(query, params)
                else:
                    result = conn.execute(query)
                df = result.df()
            
            if df.empty:
                from app.dashboard.components.charts import create_empty_figure
                return create_empty_figure("No map data available")
            
            # Create map
            return create_map_figure(
                df,
                color_column="value",
                hover_name="location",
                hover_data=["parameter", "value", "measurement_time"],
                title="Latest Sensor Readings"
            )
            
        except Exception as e:
            logger.error(f"Error updating map: {str(e)}")
            from app.dashboard.components.charts import create_empty_figure
            return create_empty_figure("Error loading map data")
