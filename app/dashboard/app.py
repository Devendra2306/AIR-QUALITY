"""
Main Dash Application for Air Quality Analysis Mini Project
Focused exclusively on the Mini Project Colab workflow & dataset:
- Direct downloads for Colab Notebook (.ipynb) and Dataset (.csv)
- Exploratory data analysis, criteria pollutant breakdowns, temporal trends
- Linear Regression vs PCA (95% Variance) vs Random Forest comparative ML
- Real-time interactive AQI simulator
"""

import dash
from dash import html, dcc
from app.config.settings import settings
from app.config.logging_config import logger
from app.dashboard.components.mini_project_layout import create_mini_project_layout
from app.dashboard.callbacks.mini_project_callbacks import (
    register_mini_project_callbacks,
    get_mini_project_df
)


class DashboardApp:
    """Main dashboard application for the Mini Project."""
    
    def __init__(self):
        self.app = dash.Dash(
            __name__,
            title="Air Quality Mini Project | AI/ML Analytics",
            external_stylesheets=["/assets/css/main.css"],
            suppress_callback_exceptions=True
        )
        self.server = self.app.server
        self._setup_layout()
        self._register_callbacks()
    
    def _setup_layout(self):
        """Setup dashboard layout with Mini Project workflow."""
        try:
            df = get_mini_project_df()
            cities = sorted(df["city"].dropna().unique().tolist()) if "city" in df.columns else ["New Delhi", "Mumbai", "Bengaluru"]
        except Exception as e:
            logger.warning(f"Could not load city list: {e}")
            cities = ["New Delhi", "Mumbai", "Bengaluru", "Hyderabad", "Chennai", "Kolkata"]
            
        self.app.layout = html.Div(
            className="app-shell",
            children=[
                create_mini_project_layout(cities)
            ]
        )
    
    def _register_callbacks(self):
        """Register all Mini Project callbacks."""
        register_mini_project_callbacks(self.app)


# Exported singleton instance for WSGI deployment
dash_app = DashboardApp()
app = dash_app.app
server = dash_app.server
