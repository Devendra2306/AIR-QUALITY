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
                from app.dashboard.callbacks.insights_callbacks import get_insights_dataframe
                df_cpcb = get_insights_dataframe()
                if not df_cpcb.empty:
                    city_map = df_cpcb.groupby('city').agg({
                        'latitude': 'first',
                        'longitude': 'first',
                        'aqi': 'mean',
                        'pm25': 'mean',
                        'pm10': 'mean'
                    }).reset_index()
                    city_map['location'] = city_map['city']
                    city_map['value'] = city_map['aqi'].round(1)
                    city_map['parameter'] = 'AQI'
                    city_map['measurement_time'] = "2020-07-01 (Latest Validated)"
                    return create_map_figure(
                        city_map,
                        color_column="value",
                        hover_name="location",
                        hover_data=["parameter", "value", "measurement_time"],
                        title="National Ambient Air Monitoring Network (26 Indian Urban Centers)"
                    )
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
            logger.info(f"Database map query failed ({e}), loading CPCB dataset map")
            try:
                from app.dashboard.callbacks.insights_callbacks import get_insights_dataframe
                df_cpcb = get_insights_dataframe()
                if not df_cpcb.empty:
                    city_map = df_cpcb.groupby('city').agg({
                        'latitude': 'first',
                        'longitude': 'first',
                        'aqi': 'mean',
                        'pm25': 'mean',
                        'pm10': 'mean'
                    }).reset_index()
                    city_map['location'] = city_map['city']
                    city_map['value'] = city_map['aqi'].round(1)
                    city_map['parameter'] = 'AQI'
                    city_map['measurement_time'] = "2020-07-01 (Latest Validated)"
                    return create_map_figure(
                        city_map,
                        color_column="value",
                        hover_name="location",
                        hover_data=["parameter", "value", "measurement_time"],
                        title="National Ambient Air Monitoring Network (26 Indian Urban Centers)"
                    )
            except Exception as err:
                logger.error(f"Fallback map error: {err}")

            from app.dashboard.components.charts import create_empty_figure
            return create_empty_figure("Error loading map data")
