"""
Machine Learning Dashboard Tab Layout
Provides dataset selection, CSV upload, model training controls,
evaluation metrics, interactive charts, and real-time AQI prediction simulator.
"""

from dash import html, dcc
from app.dashboard.components.layout import create_panel, create_metric_card, create_metric_grid


def create_ml_tab_layout() -> html.Div:
    """Create complete ML and Predictive Analytics tab layout."""
    return html.Div(
        className="ml-tab-container",
        children=[
            # Top Section: Dataset Selection & Training Controls
            create_panel(
                title="1. Dataset Configuration & ML Model Training",
                children=[
                    html.Div(
                        className="ml-config-grid",
                        children=[
                            # Left Column: Dataset Selection & Upload
                            html.Div(
                                className="ml-config-col",
                                children=[
                                    html.Label("Select Dataset Source:", className="form-label"),
                                    dcc.RadioItems(
                                        id="ml-dataset-source",
                                        options=[
                                            {"label": " Sample Multi-City Dataset (3,000+ records)", "value": "sample"},
                                            {"label": " Live DuckDB Database Measurements", "value": "database"},
                                            {"label": " Upload Your Own CSV File", "value": "upload"}
                                        ],
                                        value="sample",
                                        className="radio-group"
                                    ),
                                    html.Div(
                                        id="ml-upload-container",
                                        style={"display": "none", "marginTop": "12px"},
                                        children=[
                                            dcc.Upload(
                                                id="ml-csv-upload",
                                                children=html.Div([
                                                    html.Span("📂 Drag and Drop or ", style={"fontWeight": "600"}),
                                                    html.A("Select CSV Dataset File", style={"color": "#3b82f6", "textDecoration": "underline"})
                                                ]),
                                                className="upload-dropzone"
                                            ),
                                            html.Div(id="ml-upload-status", className="upload-status")
                                        ]
                                    ),
                                    html.Div(
                                        id="ml-dataset-info-banner",
                                        className="info-banner",
                                        children="Ready: Built-in multi-city dataset loaded (Delhi, Mumbai, Bengaluru, Kolkata, Hyderabad)."
                                    )
                                ]
                            ),
                            
                            # Right Column: Model Hyperparameters & Training Controls
                            html.Div(
                                className="ml-config-col",
                                children=[
                                    html.Div(
                                        className="form-row",
                                        children=[
                                            html.Div(
                                                className="form-group",
                                                children=[
                                                    html.Label("Target Variable:", className="form-label"),
                                                    dcc.Dropdown(
                                                        id="ml-target-column",
                                                        options=[
                                                            {"label": "Air Quality Index (AQI)", "value": "aqi"},
                                                            {"label": "PM2.5 (Fine Particulate)", "value": "pm25"},
                                                            {"label": "PM10 (Coarse Particulate)", "value": "pm10"},
                                                            {"label": "AQI Category (Classification)", "value": "aqi_category"}
                                                        ],
                                                        value="aqi",
                                                        clearable=False
                                                    )
                                                ]
                                            ),
                                            html.Div(
                                                className="form-group",
                                                children=[
                                                    html.Label("ML Algorithm:", className="form-label"),
                                                    dcc.Dropdown(
                                                        id="ml-algorithm",
                                                        options=[
                                                            {"label": "Random Forest Regressor (Ensemble)", "value": "random_forest"},
                                                            {"label": "Gradient Boosting Regressor", "value": "gradient_boosting"},
                                                            {"label": "Linear / Ridge Regression", "value": "linear_regression"},
                                                            {"label": "Decision Tree Regressor", "value": "decision_tree"}
                                                        ],
                                                        value="random_forest",
                                                        clearable=False
                                                    )
                                                ]
                                            )
                                        ]
                                    ),
                                    html.Div(
                                        className="form-row",
                                        style={"marginTop": "10px"},
                                        children=[
                                            html.Div(
                                                className="form-group",
                                                style={"flex": "1"},
                                                children=[
                                                    html.Label("Test Data Split (%):", className="form-label"),
                                                    dcc.Slider(
                                                        id="ml-test-split",
                                                        min=10,
                                                        max=40,
                                                        step=5,
                                                        value=20,
                                                        marks={10: "10%", 20: "20%", 30: "30%", 40: "40%"},
                                                        tooltip={"placement": "bottom", "always_visible": False}
                                                    )
                                                ]
                                            ),
                                            html.Div(
                                                style={"display": "flex", "alignItems": "flex-end", "paddingBottom": "10px"},
                                                children=[
                                                    html.Button(
                                                        "🚀 Train Model & Generate Visuals",
                                                        id="ml-train-btn",
                                                        n_clicks=0,
                                                        className="btn btn-primary btn-large"
                                                    )
                                                ]
                                            )
                                        ]
                                    ),
                                    html.Div(id="ml-training-status", className="status-message")
                                ]
                            )
                        ]
                    )
                ]
            ),
            
            # Middle Section: Model Performance Metrics
            html.Div(id="ml-metrics-container", className="ml-metrics-section"),
            
            # Visual Analytics Grid (2x2)
            html.Div(
                className="ml-visuals-grid",
                children=[
                    create_panel(
                        title="Model Accuracy: Actual vs. Predicted",
                        children=[
                            dcc.Loading(
                                type="circle",
                                children=dcc.Graph(
                                    id="ml-chart-actual-vs-pred",
                                    config={"displaylogo": False}
                                )
                            )
                        ]
                    ),
                    create_panel(
                        title="Pollutant Feature Importance",
                        children=[
                            dcc.Loading(
                                type="circle",
                                children=dcc.Graph(
                                    id="ml-chart-feature-importance",
                                    config={"displaylogo": False}
                                )
                            )
                        ]
                    ),
                    create_panel(
                        title="Prediction Residuals (Error Distribution)",
                        children=[
                            dcc.Loading(
                                type="circle",
                                children=dcc.Graph(
                                    id="ml-chart-residuals",
                                    config={"displaylogo": False}
                                )
                            )
                        ]
                    ),
                    create_panel(
                        title="Pollutant Correlation Matrix",
                        children=[
                            dcc.Loading(
                                type="circle",
                                children=dcc.Graph(
                                    id="ml-chart-correlation",
                                    config={"displaylogo": False}
                                )
                            )
                        ]
                    )
                ]
            ),
            
            # Bottom Section: Interactive What-If Scenario Simulator & Live Predictor
            create_panel(
                title="2. Interactive Real-Time Air Quality & AQI Predictor",
                children=[
                    html.P(
                        "Test custom pollutant and weather concentrations to simulate live predictions from the trained model.",
                        style={"color": "#64748b", "marginBottom": "16px"}
                    ),
                    html.Div(
                        className="ml-simulator-container",
                        children=[
                            # Left: Input sliders / values
                            html.Div(
                                className="ml-simulator-inputs",
                                children=[
                                    html.Div(
                                        className="simulator-grid",
                                        children=[
                                            html.Div([
                                                html.Label("PM2.5 (µg/m³):"),
                                                dcc.Input(id="sim-pm25", type="number", value=45.0, min=0, max=500, step=0.5, className="form-input")
                                            ], className="sim-field"),
                                            html.Div([
                                                html.Label("PM10 (µg/m³):"),
                                                dcc.Input(id="sim-pm10", type="number", value=85.0, min=0, max=600, step=0.5, className="form-input")
                                            ], className="sim-field"),
                                            html.Div([
                                                html.Label("NO2 (µg/m³):"),
                                                dcc.Input(id="sim-no2", type="number", value=28.0, min=0, max=400, step=0.5, className="form-input")
                                            ], className="sim-field"),
                                            html.Div([
                                                html.Label("SO2 (µg/m³):"),
                                                dcc.Input(id="sim-so2", type="number", value=14.0, min=0, max=400, step=0.5, className="form-input")
                                            ], className="sim-field"),
                                            html.Div([
                                                html.Label("CO (ppm):"),
                                                dcc.Input(id="sim-co", type="number", value=0.9, min=0, max=50, step=0.1, className="form-input")
                                            ], className="sim-field"),
                                            html.Div([
                                                html.Label("O3 (µg/m³):"),
                                                dcc.Input(id="sim-o3", type="number", value=32.0, min=0, max=400, step=0.5, className="form-input")
                                            ], className="sim-field"),
                                            html.Div([
                                                html.Label("Temperature (°C):"),
                                                dcc.Input(id="sim-temp", type="number", value=26.5, min=-10, max=55, step=0.5, className="form-input")
                                            ], className="sim-field"),
                                            html.Div([
                                                html.Label("Humidity (%):"),
                                                dcc.Input(id="sim-humidity", type="number", value=65.0, min=10, max=100, step=1, className="form-input")
                                            ], className="sim-field"),
                                            html.Div([
                                                html.Label("Wind Speed (km/h):"),
                                                dcc.Input(id="sim-wind", type="number", value=8.5, min=0, max=100, step=0.5, className="form-input")
                                            ], className="sim-field")
                                        ]
                                    ),
                                    html.Button(
                                        "⚡ Compute Live Prediction",
                                        id="sim-predict-btn",
                                        n_clicks=0,
                                        className="btn btn-primary",
                                        style={"marginTop": "14px", "width": "100%"}
                                    )
                                ]
                            ),
                            
                            # Right: Live Output Gauge & Health Card
                            html.Div(
                                className="ml-simulator-output",
                                children=[
                                    dcc.Graph(id="sim-gauge-chart", config={"displaylogo": False}),
                                    html.Div(id="sim-advice-card", className="prediction-advice-card")
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    )
