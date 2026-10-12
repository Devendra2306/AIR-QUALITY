"""
Mini Project Dashboard Layout
Complete single-app UI showcasing the Air Quality Index (AQI) Analysis Mini Project
matching the Colab notebook: 'mini project final set/Air_Quality_Mini_Project_India_Dataset (1).ipynb'
"""

from dash import html, dcc
from app.dashboard.components.layout import create_panel, create_metric_card, create_metric_grid, create_tab


def create_mini_project_layout(cities: list) -> html.Div:
    """Create complete Mini Project dashboard layout."""
    city_options = [{"label": c, "value": c} for c in cities]
    default_city = cities[0] if cities else "New Delhi"
    
    return html.Div(
        className="mini-project-container",
        style={"padding": "12px 0"},
        children=[
            # Top Academic Banner with Direct Downloads
            html.Div(
                style={
                    "background": "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
                    "color": "#ffffff",
                    "padding": "24px 28px",
                    "borderRadius": "12px",
                    "marginBottom": "20px",
                    "boxShadow": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"
                },
                children=[
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "flexWrap": "wrap", "gap": "16px"},
                        children=[
                            html.Div([
                                html.Span("🎓 ACADEMIC MINI PROJECT SHOWCASE", style={
                                    "background": "rgba(59, 130, 246, 0.25)",
                                    "color": "#93c5fd",
                                    "padding": "4px 12px",
                                    "borderRadius": "20px",
                                    "fontSize": "0.75rem",
                                    "fontWeight": "700",
                                    "letterSpacing": "0.06em",
                                    "display": "inline-block",
                                    "marginBottom": "10px"
                                }),
                                html.H1("Air Quality Index (AQI) Analysis Mini Project", style={
                                    "margin": "0 0 8px 0",
                                    "fontSize": "1.75rem",
                                    "fontWeight": "800",
                                    "color": "#ffffff"
                                }),
                                html.P(
                                    "End-to-end data pipeline, exploratory analysis, PCA dimensionality reduction, and comparative machine learning (Linear Regression vs. PCA vs. Random Forest).",
                                    style={"margin": "0", "color": "#94a3b8", "fontSize": "0.95rem", "maxWidth": "850px", "lineHeight": "1.5"}
                                )
                            ]),
                            html.Div(
                                style={"display": "flex", "gap": "12px", "flexWrap": "wrap"},
                                children=[
                                    html.A(
                                        "📥 Download Colab Notebook (.ipynb)",
                                        href="/assets/Air_Quality_Mini_Project.ipynb",
                                        download="Air_Quality_Mini_Project.ipynb",
                                        className="btn btn-primary",
                                        style={
                                            "textDecoration": "none",
                                            "padding": "10px 18px",
                                            "fontSize": "0.85rem",
                                            "fontWeight": "600",
                                            "backgroundColor": "#2563eb",
                                            "color": "#ffffff",
                                            "borderRadius": "8px",
                                            "display": "inline-flex",
                                            "alignItems": "center"
                                        }
                                    ),
                                    html.A(
                                        "📊 Download Project Dataset (.csv)",
                                        href="/assets/sample_air_quality_dataset.csv",
                                        download="sample_air_quality_dataset.csv",
                                        className="btn btn-secondary",
                                        style={
                                            "textDecoration": "none",
                                            "padding": "10px 18px",
                                            "fontSize": "0.85rem",
                                            "fontWeight": "600",
                                            "backgroundColor": "#334155",
                                            "color": "#ffffff",
                                            "borderRadius": "8px",
                                            "display": "inline-flex",
                                            "alignItems": "center"
                                        }
                                    ),
                                    html.A(
                                        "🚀 Open in Google Colab",
                                        href="https://colab.research.google.com",
                                        target="_blank",
                                        rel="noopener noreferrer",
                                        className="btn btn-outline",
                                        style={
                                            "textDecoration": "none",
                                            "padding": "10px 16px",
                                            "fontSize": "0.85rem",
                                            "fontWeight": "600",
                                            "backgroundColor": "transparent",
                                            "border": "1px solid #475569",
                                            "color": "#e2e8f0",
                                            "borderRadius": "8px",
                                            "display": "inline-flex",
                                            "alignItems": "center"
                                        }
                                    )
                                ]
                            )
                        ]
                    )
                ]
            ),
            
            # Executive Metric Cards
            html.Div(id="mini-kpi-cards", className="summary-section"),
            
            # Main Project Tabs
            dcc.Tabs(
                id="mini-project-tabs",
                value="tab-eda",
                children=[
                    # TAB 1: Exploratory Data Analysis (Steps 1 to 7)
                    create_tab(
                        label="📊 Steps 1–7: Exploratory Data Analysis & Trends",
                        value="tab-eda",
                        children=[
                            # Section 1: AQI Distribution & Category Breakdown
                            html.Div(
                                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(450px, 1fr))", "gap": "16px", "marginTop": "16px"},
                                children=[
                                    create_panel(
                                        title="Step 4: Air Quality Index (AQI) Distribution & Spread",
                                        children=[dcc.Graph(id="chart-aqi-dist", config={"displaylogo": False})]
                                    ),
                                    create_panel(
                                        title="Step 4: AQI Category Proportions (CPCB Standard)",
                                        children=[dcc.Graph(id="chart-category-pie", config={"displaylogo": False})]
                                    )
                                ]
                            ),
                            
                            # Section 2: Criteria Pollutant Severity Breakdown
                            html.Div(
                                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(450px, 1fr))", "gap": "16px", "marginTop": "16px"},
                                children=[
                                    create_panel(
                                        title="Step 5: Criteria Pollutants Mean Concentrations",
                                        children=[dcc.Graph(id="chart-pollutant-means", config={"displaylogo": False})]
                                    ),
                                    create_panel(
                                        title="Step 5: Urban Airshed Severity Comparison (PM2.5 / PM10 / AQI)",
                                        children=[dcc.Graph(id="chart-city-pollutants", config={"displaylogo": False})]
                                    )
                                ]
                            ),
                            
                            # Section 3: Longitudinal Trends & Correlation Heatmap
                            html.Div(
                                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(450px, 1fr))", "gap": "16px", "marginTop": "16px"},
                                children=[
                                    create_panel(
                                        title="Step 6: AQI Over Time (Temporal Trajectory)",
                                        children=[
                                            html.Div(
                                                style={"display": "flex", "alignItems": "center", "gap": "12px", "marginBottom": "12px"},
                                                children=[
                                                    html.Label("Filter Urban Airshed:", style={"fontWeight": "600", "fontSize": "0.9rem"}),
                                                    dcc.Dropdown(
                                                        id="mini-trend-city",
                                                        options=[{"label": "All Urban Airsheds (Aggregate)", "value": "ALL"}] + city_options,
                                                        value="ALL",
                                                        clearable=False,
                                                        style={"width": "260px"}
                                                    )
                                                ]
                                            ),
                                            dcc.Graph(id="chart-temporal-trend", config={"displaylogo": False})
                                        ]
                                    ),
                                    create_panel(
                                        title="Step 7: Inter-Pollutant & Weather Correlation Matrix",
                                        children=[dcc.Graph(id="chart-correlation-heatmap", config={"displaylogo": False})]
                                    )
                                ]
                            )
                        ]
                    ),
                    
                    # TAB 2: Machine Learning & PCA (Steps 8 to 10)
                    create_tab(
                        label="🤖 Steps 8–10: ML Models & PCA Dimensionality Reduction",
                        value="tab-ml",
                        children=[
                            html.Div(
                                style={"marginTop": "16px"},
                                children=[
                                    # Section: Dataset Source & Custom File Upload
                                    create_panel(
                                        title="Step 8: Dataset Configuration & Training Source",
                                        children=[
                                            html.Div(
                                                style={"display": "flex", "flexWrap": "wrap", "gap": "20px", "alignItems": "flex-start"},
                                                children=[
                                                    html.Div(
                                                        style={"flex": "1", "minWidth": "300px"},
                                                        children=[
                                                            html.Label("Select Training Data Source:", style={"fontWeight": "600", "fontSize": "0.95rem"}),
                                                            dcc.RadioItems(
                                                                id="mini-dataset-source",
                                                                options=[
                                                                    {"label": " Built-in Project Dataset (3,133 Indian City Records)", "value": "default"},
                                                                    {"label": " Upload Custom CSV or ZIP Dataset", "value": "upload"}
                                                                ],
                                                                value="default",
                                                                className="radio-group"
                                                            ),
                                                            html.Div(
                                                                id="mini-upload-container",
                                                                style={"display": "none", "marginTop": "12px"},
                                                                children=[
                                                                    dcc.Upload(
                                                                        id="mini-csv-upload",
                                                                        children=html.Div([
                                                                            html.Span("📂 Drag & Drop or ", style={"fontWeight": "600"}),
                                                                            html.A("Select CSV or ZIP File", style={"color": "#2563eb", "textDecoration": "underline"})
                                                                        ]),
                                                                        accept=".csv,.zip",
                                                                        style={
                                                                            "border": "2px dashed #93c5fd",
                                                                            "borderRadius": "8px",
                                                                            "padding": "18px",
                                                                            "textAlign": "center",
                                                                            "backgroundColor": "#f8fafc",
                                                                            "cursor": "pointer"
                                                                        }
                                                                    ),
                                                                    html.Div(id="mini-upload-status", style={"marginTop": "8px"})
                                                                ]
                                                            )
                                                        ]
                                                    ),
                                                    html.Div(
                                                        style={"flex": "1", "minWidth": "300px"},
                                                        children=[
                                                            html.Div(
                                                                id="mini-dataset-banner",
                                                                style={"padding": "14px", "backgroundColor": "#eff6ff", "border": "1px solid #bfdbfe", "borderRadius": "8px", "color": "#1e40af", "fontSize": "0.9rem", "lineHeight": "1.5"},
                                                                children="Active Source: Built-in Mini Project Dataset (3,133 observations across 6 Indian cities). All models and visuals are trained on this data."
                                                            ),
                                                            html.Button(
                                                                "🚀 Retrain Models on Selected Source",
                                                                id="mini-retrain-btn",
                                                                n_clicks=0,
                                                                className="btn btn-primary",
                                                                style={"marginTop": "12px", "padding": "10px 18px", "fontWeight": "600", "backgroundColor": "#2563eb", "color": "#ffffff", "borderRadius": "6px", "border": "none", "cursor": "pointer"}
                                                            ),
                                                            html.Div(id="mini-retrain-status", style={"marginTop": "8px"})
                                                        ]
                                                    )
                                                ]
                                            )
                                        ]
                                    ),
                                    
                                    create_panel(
                                        title="Step 9: Comparative Model Performance Evaluation",
                                        children=[
                                            html.P(
                                                "Rigorous comparison between Standard Linear Regression, PCA (95% Variance Retained) + Linear Regression, and Random Forest Regressor on hold-out test set (20% split).",
                                                style={"color": "#64748b", "marginBottom": "12px"}
                                            ),
                                            html.Div(id="mini-model-comparison-table")
                                        ]
                                    ),
                                    
                                    html.Div(
                                        style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(450px, 1fr))", "gap": "16px", "marginTop": "16px"},
                                        children=[
                                            create_panel(
                                                title="Step 10: Actual vs. Predicted AQI (with Ideal Prediction Line)",
                                                children=[
                                                    html.Div(
                                                        style={"display": "flex", "alignItems": "center", "gap": "12px", "marginBottom": "12px"},
                                                        children=[
                                                            html.Label("Select Model:", style={"fontWeight": "600", "fontSize": "0.9rem"}),
                                                            dcc.RadioItems(
                                                                id="mini-model-select",
                                                                options=[
                                                                    {"label": " PCA + Linear Regression", "value": "pca"},
                                                                    {"label": " Standard Linear Regression", "value": "lr"},
                                                                    {"label": " Random Forest Regressor", "value": "rf"}
                                                                ],
                                                                value="pca",
                                                                className="radio-group"
                                                            )
                                                        ]
                                                    ),
                                                    dcc.Graph(id="chart-actual-vs-pred", config={"displaylogo": False})
                                                ]
                                            ),
                                            create_panel(
                                                title="Step 8: PCA Scree Plot — Explained Variance Ratio",
                                                children=[dcc.Graph(id="chart-pca-scree", config={"displaylogo": False})]
                                            )
                                        ]
                                    )
                                ]
                            )
                        ]
                    ),
                    
                    # TAB 3: Live AQI Prediction Simulator
                    create_tab(
                        label="⚡ Live AQI Prediction Simulator",
                        value="tab-sim",
                        children=[
                            html.Div(
                                style={"marginTop": "16px"},
                                children=[
                                    create_panel(
                                        title="Interactive Multi-Pollutant AQI Simulator",
                                        children=[
                                            html.P(
                                                "Adjust criteria pollutant concentrations and meteorological parameters to simulate real-time AQI prediction using the trained machine learning pipeline.",
                                                style={"color": "#64748b", "marginBottom": "20px"}
                                            ),
                                            html.Div(
                                                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(320px, 1fr))", "gap": "24px"},
                                                children=[
                                                    # Left Column: Inputs
                                                    html.Div([
                                                        html.Div(
                                                            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px"},
                                                            children=[
                                                                html.Div([
                                                                    html.Label("PM2.5 (µg/m³):", style={"fontWeight": "600"}),
                                                                    dcc.Slider(id="sim-pm25", min=5, max=300, step=5, value=45, tooltip={"placement": "bottom", "always_visible": True})
                                                                ]),
                                                                html.Div([
                                                                    html.Label("PM10 (µg/m³):", style={"fontWeight": "600"}),
                                                                    dcc.Slider(id="sim-pm10", min=10, max=500, step=10, value=85, tooltip={"placement": "bottom", "always_visible": True})
                                                                ]),
                                                                html.Div([
                                                                    html.Label("NO2 (µg/m³):", style={"fontWeight": "600"}),
                                                                    dcc.Slider(id="sim-no2", min=5, max=150, step=5, value=28, tooltip={"placement": "bottom", "always_visible": True})
                                                                ]),
                                                                html.Div([
                                                                    html.Label("SO2 (µg/m³):", style={"fontWeight": "600"}),
                                                                    dcc.Slider(id="sim-so2", min=2, max=100, step=2, value=14, tooltip={"placement": "bottom", "always_visible": True})
                                                                ]),
                                                                html.Div([
                                                                    html.Label("CO (mg/m³):", style={"fontWeight": "600"}),
                                                                    dcc.Slider(id="sim-co", min=0.1, max=10.0, step=0.2, value=0.9, tooltip={"placement": "bottom", "always_visible": True})
                                                                ]),
                                                                html.Div([
                                                                    html.Label("O3 (µg/m³):", style={"fontWeight": "600"}),
                                                                    dcc.Slider(id="sim-o3", min=5, max=150, step=5, value=32, tooltip={"placement": "bottom", "always_visible": True})
                                                                ]),
                                                                html.Div([
                                                                    html.Label("Temperature (°C):", style={"fontWeight": "600"}),
                                                                    dcc.Slider(id="sim-temp", min=10, max=45, step=1, value=26, tooltip={"placement": "bottom", "always_visible": True})
                                                                ]),
                                                                html.Div([
                                                                    html.Label("Humidity (%):", style={"fontWeight": "600"}),
                                                                    dcc.Slider(id="sim-humidity", min=10, max=100, step=5, value=65, tooltip={"placement": "bottom", "always_visible": True})
                                                                ]),
                                                                html.Div([
                                                                    html.Label("Wind Speed (km/h):", style={"fontWeight": "600"}),
                                                                    dcc.Slider(id="sim-wind", min=1, max=30, step=1, value=8, tooltip={"placement": "bottom", "always_visible": True})
                                                                ])
                                                            ]
                                                        )
                                                    ]),
                                                    
                                                    # Right Column: Output Gauge & Advice
                                                    html.Div([
                                                        dcc.Graph(id="sim-gauge", config={"displaylogo": False}),
                                                        html.Div(id="sim-advisory-card", style={"marginTop": "12px"})
                                                    ])
                                                ]
                                            )
                                        ]
                                    )
                                ]
                            )
                        ]
                    ),
                    
                    # TAB 4: Colab Notebook & Key Insights (Step 11)
                    create_tab(
                        label="📘 Step 11: Project Conclusions & Colab Reference",
                        value="tab-notes",
                        children=[
                            html.Div(
                                style={"marginTop": "16px"},
                                children=[
                                    create_panel(
                                        title="Step 11: Key Academic Findings & Conclusions",
                                        children=[
                                            html.Div(
                                                style={"background": "#f8fafc", "border": "1px solid #e2e8f0", "borderRadius": "8px", "padding": "20px", "marginBottom": "20px"},
                                                children=[
                                                    html.H4("Summary of Key Findings (from Notebook Cell 24):", style={"margin": "0 0 12px 0", "color": "#0f172a"}),
                                                    html.Ul(
                                                        style={"color": "#334155", "lineHeight": "1.8", "fontSize": "0.95rem", "paddingLeft": "20px"},
                                                        children=[
                                                            html.Li("The AQI histogram reflects a wide variance across monitored Indian urban centers, with PM2.5 and PM10 acting as primary drivers of elevated AQI index values."),
                                                            html.Li("Pollutant summaries and the correlation matrix establish strong linear correlation (r > 0.85) between fine particulate matter (PM2.5) and overall ambient AQI."),
                                                            html.Li("PCA dimensionality reduction successfully retains >96.8% of total dataset variance using just 6 orthogonal principal components, effectively mitigating multicollinearity without sacrificing model predictive fidelity."),
                                                            html.Li("Linear Regression and PCA + Linear Regression achieved strong predictive accuracy (R² = 0.928 and R² = 0.926 respectively), with Mean Absolute Error below 5.1 AQI units."),
                                                            html.Li("Ensemble non-linear modeling (Random Forest) achieved near-perfect reconstruction (R² = 0.999, MAE = 0.32), validating the consistency of the underlying EPA / CPCB sub-index formulations.")
                                                        ]
                                                    )
                                                ]
                                            ),
                                            html.Div(
                                                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(280px, 1fr))", "gap": "16px"},
                                                children=[
                                                    html.Div(
                                                        style={"border": "1px solid #e2e8f0", "borderRadius": "8px", "padding": "16px", "backgroundColor": "#ffffff"},
                                                        children=[
                                                            html.H4("📓 Colab Notebook Structure", style={"margin": "0 0 10px 0", "color": "#2563eb"}),
                                                            html.P("Contains all 11 cells ready to run on Google Colab or JupyterLab with zero dependencies required.", style={"fontSize": "0.85rem", "color": "#64748b"}),
                                                            html.A("Download Air_Quality_Mini_Project.ipynb", href="/assets/Air_Quality_Mini_Project.ipynb", download="Air_Quality_Mini_Project.ipynb", style={"color": "#2563eb", "fontWeight": "600", "fontSize": "0.85rem"})
                                                        ]
                                                    ),
                                                    html.Div(
                                                        style={"border": "1px solid #e2e8f0", "borderRadius": "8px", "padding": "16px", "backgroundColor": "#ffffff"},
                                                        children=[
                                                            html.H4("📊 Cleaned Project Dataset", style={"margin": "0 0 10px 0", "color": "#10b981"}),
                                                            html.P("3,133 daily observations across 6 Indian cities with complete pollutant and meteorological readings.", style={"fontSize": "0.85rem", "color": "#64748b"}),
                                                            html.A("Download sample_air_quality_dataset.csv", href="/assets/sample_air_quality_dataset.csv", download="sample_air_quality_dataset.csv", style={"color": "#10b981", "fontWeight": "600", "fontSize": "0.85rem"})
                                                        ]
                                                    ),
                                                    html.Div(
                                                        style={"border": "1px solid #e2e8f0", "borderRadius": "8px", "padding": "16px", "backgroundColor": "#ffffff"},
                                                        children=[
                                                            html.H4("🌐 Production Deployment", style={"margin": "0 0 10px 0", "color": "#8b5cf6"}),
                                                            html.P("Optimized for Render Free Tier (512MB RAM) using lightweight Plotly rendering and single-worker Gthread architecture.", style={"fontSize": "0.85rem", "color": "#64748b"}),
                                                            html.Span("✓ Render Production Ready", style={"color": "#8b5cf6", "fontWeight": "600", "fontSize": "0.85rem"})
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
                ]
            )
        ]
    )
