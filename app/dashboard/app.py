import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
from app.config.settings import settings
from app.config.logging_config import logger
from app.core.database import db_manager
from app.dashboard.components.layout import (
    create_header,
    create_metric_card,
    create_metric_grid,
    create_tab,
    create_panel,
    create_empty_state
)
from app.dashboard.components.charts import (
    create_empty_figure,
    style_figure,
    create_line_chart,
    create_box_plot,
    create_bar_chart
)
from app.dashboard.callbacks.map_callbacks import register_map_callbacks


class DashboardApp:
    """Main dashboard application."""
    
    def __init__(self):
        self.app = dash.Dash(
            __name__,
            title=settings.APP_NAME,
            external_stylesheets=["/assets/css/main.css"],
            suppress_callback_exceptions=True
        )
        self.server = self.app.server
        self._setup_layout()
        self._register_callbacks()
    
    def _setup_layout(self):
        """Setup dashboard layout."""
        self.app.layout = html.Div(
            className="app-shell",
            children=[
                # Auto-refresh interval
                dcc.Interval(
                    id="refresh-interval",
                    interval=settings.DASH_REFRESH_INTERVAL * 1000,
                    n_intervals=0
                ),
                
                # Download component
                dcc.Download(id="download-data"),
                
                # Header
                create_header(
                    title=settings.APP_NAME,
                    subtitle="Real-time Environmental Data Dashboard"
                ),
                
                # Summary cards
                html.Div(id="summary-cards", className="summary-section"),
                
                # Tabs
                dcc.Tabs(
                    id="main-tabs",
                    value="map-tab",
                    children=[
                        create_tab(
                            label="Map View",
                            value="map-tab",
                            children=[
                                create_panel(
                                    children=[
                                        html.Div(
                                            className="filters",
                                            children=[
                                                html.Label("Location Filter:"),
                                                dcc.Dropdown(
                                                    id="location-filter",
                                                    placeholder="All Locations",
                                                    clearable=True
                                                ),
                                                html.Label("Parameter Filter:"),
                                                dcc.Dropdown(
                                                    id="parameter-filter",
                                                    placeholder="All Parameters",
                                                    options=[
                                                        {"label": "PM2.5", "value": "pm25"},
                                                        {"label": "PM10", "value": "pm10"},
                                                        {"label": "NO2", "value": "no2"},
                                                        {"label": "SO2", "value": "so2"},
                                                        {"label": "O3", "value": "o3"},
                                                    ]
                                                )
                                            ]
                                        ),
                                        dcc.Graph(
                                            id="map-view",
                                            config={"displaylogo": False},
                                            className="graph-container"
                                        )
                                    ]
                                )
                            ]
                        ),
                        create_tab(
                            label="Trends",
                            value="trends-tab",
                            children=[
                                create_panel(
                                    children=[
                                        html.Div(
                                            className="trend-controls",
                                            children=[
                                                html.Label("Location:"),
                                                dcc.Dropdown(id="trend-location"),
                                                html.Label("Parameter:"),
                                                dcc.Dropdown(id="trend-parameter"),
                                                html.Label("Date Range:"),
                                                dcc.DatePickerRange(id="trend-date-range")
                                            ]
                                        ),
                                        html.Div(
                                            className="trend-charts",
                                            children=[
                                                dcc.Graph(id="trend-line-chart"),
                                                dcc.Graph(id="trend-box-chart")
                                            ]
                                        )
                                    ]
                                )
                            ]
                        ),
                        create_tab(
                            label="Data Quality",
                            value="quality-tab",
                            children=[
                                html.Div(id="quality-cards"),
                                create_panel(
                                    children=[
                                        dcc.Graph(id="quality-parameter-chart"),
                                        dcc.Graph(id="quality-location-chart")
                                    ]
                                )
                            ]
                        ),
                        create_tab(
                            label="Export",
                            value="export-tab",
                            children=[
                                create_panel(
                                    title="Export Data",
                                    children=[
                                        html.Div(
                                            className="export-controls",
                                            children=[
                                                html.Label("Format:"),
                                                dcc.Dropdown(
                                                    id="export-format",
                                                    options=[
                                                        {"label": "CSV", "value": "csv"},
                                                        {"label": "JSON", "value": "json"},
                                                        {"label": "Excel", "value": "excel"},
                                                        {"label": "Parquet", "value": "parquet"}
                                                    ],
                                                    value="csv"
                                                ),
                                                html.Label("Location:"),
                                                dcc.Dropdown(id="export-location"),
                                                html.Label("Parameter:"),
                                                dcc.Dropdown(id="export-parameter"),
                                                html.Button(
                                                    "Download",
                                                    id="export-button",
                                                    n_clicks=0,
                                                    className="btn btn-primary"
                                                )
                                            ]
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    
    def _register_callbacks(self):
        """Register all callbacks."""
        register_map_callbacks(self.app)
        self._register_summary_callbacks()
        self._register_trend_callbacks()
        self._register_quality_callbacks()
        self._register_export_callbacks()
        self._register_filter_callbacks()
    
    def _register_summary_callbacks(self):
        """Register summary card callbacks."""
        
        @self.app.callback(
            Output("summary-cards", "children"),
            Input("refresh-interval", "n_intervals")
        )
        def update_summary(n):
            """Update summary cards."""
            try:
                # Get summary statistics
                query = """
                SELECT 
                    COUNT(DISTINCT location_id) as location_count,
                    COUNT(DISTINCT parameter) as parameter_count,
                    COUNT(*) as total_measurements,
                    MAX(measurement_time) as latest_measurement
                FROM raw.measurements
                WHERE quality_score > 0.5
                """
                
                with db_manager.get_connection() as conn:
                    result = conn.execute(query)
                    stats = result.fetchone()
                
                if not stats or stats[0] == 0:
                    return create_empty_state("No data available yet")
                
                cards = create_metric_grid([
                    create_metric_card("Locations", str(stats[0]), "blue"),
                    create_metric_card("Parameters", str(stats[1]), "green"),
                    create_metric_card("Measurements", f"{stats[2]:,}", "amber"),
                    create_metric_card(
                        "Latest Update",
                        stats[3].strftime("%H:%M") if stats[3] else "N/A",
                        "red"
                    )
                ])
                
                return cards
                
            except Exception as e:
                logger.error(f"Error updating summary: {str(e)}")
                return create_empty_state("Error loading summary")
    
    def _register_trend_callbacks(self):
        """Register trend chart callbacks."""
        
        @self.app.callback(
            [Output("trend-line-chart", "figure"),
             Output("trend-box-chart", "figure")],
            [Input("refresh-interval", "n_intervals"),
             State("trend-location", "value"),
             State("trend-parameter", "value"),
             State("trend-date-range", "start_date"),
             State("trend-date-range", "end_date")]
        )
        def update_trends(n, location, parameter, start_date, end_date):
            """Update trend charts."""
            try:
                query = """
                SELECT 
                    measurement_time,
                    value,
                    parameter
                FROM raw.measurements
                WHERE quality_score > 0.5
                """
                
                params = {}
                if location:
                    query += " AND location_id = $location_id"
                    params["location_id"] = location
                if parameter:
                    query += " AND parameter = $parameter"
                    params["parameter"] = parameter
                if start_date:
                    query += " AND measurement_time >= $start_date"
                    params["start_date"] = start_date
                if end_date:
                    query += " AND measurement_time <= $end_date"
                    params["end_date"] = end_date
                
                query += " ORDER BY measurement_time DESC LIMIT 1000"
                
                with db_manager.get_connection() as conn:
                    if params:
                        result = conn.execute(query, params)
                    else:
                        result = conn.execute(query)
                    df = result.df()
                
                if df.empty:
                    return create_empty_figure("No trend data"), create_empty_figure("No trend data")
                
                df["measurement_time"] = pd.to_datetime(df["measurement_time"])
                
                line_fig = create_line_chart(
                    df,
                    "measurement_time",
                    "value",
                    f"{parameter.upper()} Trend" if parameter else "Measurement Trend"
                )
                
                box_fig = create_box_plot(
                    df,
                    "parameter",
                    "value",
                    "Value Distribution"
                )
                
                return line_fig, box_fig
                
            except Exception as e:
                logger.error(f"Error updating trends: {str(e)}")
                return create_empty_figure("Error"), create_empty_figure("Error")
    
    def _register_quality_callbacks(self):
        """Register quality callbacks."""
        
        @self.app.callback(
            [Output("quality-cards", "children"),
             Output("quality-parameter-chart", "figure"),
             Output("quality-location-chart", "figure")],
            Input("refresh-interval", "n_intervals")
        )
        def update_quality(n):
            """Update quality metrics."""
            try:
                query = """
                SELECT 
                    parameter,
                    COUNT(*) as count,
                    AVG(quality_score) as avg_quality
                FROM raw.measurements
                GROUP BY parameter
                """
                
                with db_manager.get_connection() as conn:
                    result = conn.execute(query)
                    df = result.df()
                
                if df.empty:
                    return create_empty_state("No quality data"), create_empty_figure(), create_empty_figure()
                
                cards = create_metric_grid([
                    create_metric_card("Avg Quality", f"{df['avg_quality'].mean():.2f}", "green"),
                    create_metric_card("Total Records", f"{df['count'].sum():,}", "blue"),
                    create_metric_card("Parameters", str(len(df)), "amber")
                ], columns=3)
                
                param_fig = create_bar_chart(
                    df,
                    "parameter",
                    "count",
                    "Records by Parameter"
                )
                
                return cards, param_fig, create_empty_figure("Location quality coming soon")
                
            except Exception as e:
                logger.error(f"Error updating quality: {str(e)}")
                return create_empty_state("Error"), create_empty_figure(), create_empty_figure()
    
    def _register_export_callbacks(self):
        """Register export callbacks."""
        
        @self.app.callback(
            Output("download-data", "data"),
            Input("export-button", "n_clicks"),
            [State("export-format", "value"),
             State("export-location", "value"),
             State("export-parameter", "value")]
        )
        def export_data(n_clicks, format, location, parameter):
            """Export data."""
            if n_clicks == 0:
                return None
            
            try:
                from app.services.export_service import ExportService
                export_service = ExportService()
                
                data = export_service.get_export_data(
                    format=format,
                    location_id=location,
                    parameter=parameter
                )
                
                filename = f"air_quality_export_{format}"
                
                from dash.dcc import send_bytes
                return send_bytes(data, filename=f"{filename}.{format}")
                
            except Exception as e:
                logger.error(f"Error exporting data: {str(e)}")
                return None
    
    def _register_filter_callbacks(self):
        """Register filter dropdown callbacks."""
        
        @self.app.callback(
            [Output("location-filter", "options"),
             Output("trend-location", "options"),
             Output("export-location", "options")],
            Input("refresh-interval", "n_intervals")
        )
        def update_location_options(n):
            """Update location dropdown options."""
            try:
                query = """
                SELECT DISTINCT location_id, location
                FROM presentation.location_summary
                ORDER BY location
                """
                
                with db_manager.get_connection() as conn:
                    result = conn.execute(query)
                    df = result.df()
                
                if df.empty:
                    return [], [], []
                
                options = [{"label": row["location"], "value": row["location_id"]} 
                          for _, row in df.iterrows()]
                
                return options, options, options
                
            except Exception as e:
                logger.error(f"Error updating location options: {str(e)}")
                return [], [], []
    
    def run(self, host="0.0.0.0", port=None, debug=False):
        """Run the dashboard."""
        port = port or settings.PORT
        logger.info(f"Starting dashboard on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


# Create global app instance
dashboard_app = DashboardApp()
app = dashboard_app.app
server = dashboard_app.server


if __name__ == "__main__":
    dashboard_app.run(debug=settings.DEBUG)
