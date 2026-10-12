"""
AI/ML Curriculum Insights Tab Layout
Showcases the 10 college laboratory experiments with live interactive widgets:
- A* Heuristic Clean-Air Route Planner
- Statistical Hypothesis Testing (Metro vs Regional)
- K-Means Unsupervised Zone Clustering & Elbow Validation
- 2D PCA Dimensionality Reduction
- Algorithm Benchmark Performance Leaderboard
"""

from dash import html, dcc
from app.dashboard.components.layout import create_panel, create_metric_card, create_metric_grid


def create_insights_tab_layout(city_options: list, station_options: list = None) -> html.Div:
    """Create the interactive AI/ML Research Insights tab layout."""
    default_origin = "Delhi" if "Delhi" in city_options else (city_options[0] if city_options else "Delhi")
    default_dest = "Bengaluru" if "Bengaluru" in city_options else (city_options[-1] if city_options else "Bengaluru")

    return html.Div(
        className="insights-tab-container",
        style={"padding": "16px 0"},
        children=[
            # Academic Banner
            html.Div(
                style={
                    "background": "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)",
                    "color": "#ffffff",
                    "padding": "20px 24px",
                    "borderRadius": "12px",
                    "marginBottom": "24px",
                    "boxShadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
                },
                children=[
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "flexWrap": "wrap", "gap": "12px"},
                        children=[
                            html.Div([
                                html.Span("🎓 AI/ML MINI PROJECT", style={
                                    "background": "rgba(59, 130, 246, 0.2)",
                                    "color": "#60a5fa",
                                    "padding": "4px 10px",
                                    "borderRadius": "6px",
                                    "fontSize": "0.75rem",
                                    "fontWeight": "700",
                                    "letterSpacing": "0.05em",
                                    "display": "inline-block",
                                    "marginBottom": "8px"
                                }),
                                html.H2("Air Quality AI/ML Intelligence Hub", style={
                                    "margin": "0 0 6px 0",
                                    "fontSize": "1.5rem",
                                    "fontWeight": "700",
                                    "color": "#ffffff"
                                }),
                                html.P(
                                    "Advanced machine learning analytics and heuristic decision support trained on 29,531 daily records across 26 Indian cities.",
                                    style={"margin": "0", "color": "#94a3b8", "fontSize": "0.95rem"}
                                )
                            ]),
                            html.Div(
                                style={"display": "flex", "gap": "10px"},
                                children=[
                                    html.A(
                                        "📖 Open Google Colab Notebook",
                                        href="https://colab.research.google.com",
                                        target="_blank",
                                        className="btn btn-primary",
                                        style={"textDecoration": "none", "display": "inline-flex", "alignItems": "center"}
                                    )
                                ]
                            )
                        ]
                    )
                ]
            ),

            # SECTION 1: A* SEARCH CLEAN-AIR NAVIGATION
            create_panel(
                title="AI Heuristic Search — A* Clean-Air Travel Navigation Corridor",
                children=[
                    html.P(
                        "Formulation: Uses the A* pathfinding algorithm where the cost function f(n) = g(n) + h(n) balances physical travel distance (haversine) and ambient pollutant toxicity penalty to route travelers along the cleanest atmospheric corridor.",
                        style={"color": "#64748b", "marginBottom": "16px"}
                    ),
                    html.Div(
                        className="form-row",
                        style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "alignItems": "flex-end", "marginBottom": "16px"},
                        children=[
                            html.Div(
                                style={"flex": "1", "minWidth": "200px"},
                                children=[
                                    html.Label("Origin City (Start Node):", className="form-label", style={"fontWeight": "600"}),
                                    dcc.Dropdown(
                                        id="astar-origin-city",
                                        options=[{"label": c, "value": c} for c in city_options],
                                        value=default_origin,
                                        clearable=False
                                    )
                                ]
                            ),
                            html.Div(
                                style={"flex": "1", "minWidth": "200px"},
                                children=[
                                    html.Label("Destination City (Goal Node):", className="form-label", style={"fontWeight": "600"}),
                                    dcc.Dropdown(
                                        id="astar-dest-city",
                                        options=[{"label": c, "value": c} for c in city_options],
                                        value=default_dest,
                                        clearable=False
                                    )
                                ]
                            ),
                            html.Div(
                                style={"flex": "1.2", "minWidth": "240px"},
                                children=[
                                    html.Label("Cleanliness Priority (Toxicity Penalty Weight):", className="form-label", style={"fontWeight": "600"}),
                                    dcc.Slider(
                                        id="astar-toxicity-weight",
                                        min=0.1,
                                        max=1.0,
                                        step=0.1,
                                        value=0.6,
                                        marks={0.1: "Speed", 0.5: "Balanced", 1.0: "Pure Clean Air"},
                                        tooltip={"placement": "bottom", "always_visible": False}
                                    )
                                ]
                            ),
                            html.Div(
                                children=[
                                    html.Button(
                                        "⚡ Compute Optimal A* Route",
                                        id="astar-compute-btn",
                                        n_clicks=0,
                                        className="btn btn-primary"
                                    )
                                ]
                            )
                        ]
                    ),
                    html.Div(id="astar-metrics-container", style={"marginBottom": "16px"}),
                    dcc.Loading(
                        type="circle",
                        children=dcc.Graph(id="astar-route-graph", config={"displaylogo": False})
                    ),
                    html.Div(id="astar-route-summary", style={"marginTop": "12px"})
                ]
            ),

            # SECTION 2: STATISTICAL HYPOTHESIS TESTING (T-TEST)
            html.Div(style={"marginTop": "24px"}),
            create_panel(
                title="Statistical Hypothesis Testing — Indo-Gangetic Basin vs. Coastal Dispersion",
                children=[
                    html.P(
                        "Null Hypothesis (H₀): Mean AQI in landlocked Indo-Gangetic cities equals coastal/peninsular cities. Alternative Hypothesis (H₁): Indo-Gangetic AQI is significantly higher due to geographic thermal inversion and winter atmospheric stagnation.",
                        style={"color": "#64748b", "marginBottom": "16px"}
                    ),
                    html.Div(id="ttest-metrics-container", style={"marginBottom": "16px"}),
                    dcc.Loading(
                        type="circle",
                        children=dcc.Graph(id="ttest-box-graph", config={"displaylogo": False})
                    )
                ]
            ),

            # SECTION 3: K-MEANS CLUSTERING & ELBOW VALIDATION
            html.Div(style={"marginTop": "24px"}),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(480px, 1fr))", "gap": "20px"},
                children=[
                    create_panel(
                        title="K-Means Unsupervised Zone Clustering",
                        children=[
                            html.P(
                                "Partitions Indian monitoring stations and cities into 3 distinct environmental risk profiles using multi-pollutant feature vectors (PM2.5, PM10, NO2, SO2, CO).",
                                style={"color": "#64748b", "marginBottom": "12px"}
                            ),
                            dcc.Loading(
                                type="circle",
                                children=dcc.Graph(id="kmeans-scatter-graph", config={"displaylogo": False})
                            ),
                            html.Div(id="kmeans-table-container", style={"marginTop": "12px"})
                        ]
                    ),
                    create_panel(
                        title="Cluster Optimization: The Elbow Method (k=3)",
                        children=[
                            html.P(
                                "Mathematical validation of optimal cluster count (k) by measuring the rate of decrease in within-cluster inertia (sum of squared errors). The inflection point occurs at k = 3.",
                                style={"color": "#64748b", "marginBottom": "12px"}
                            ),
                            dcc.Loading(
                                type="circle",
                                children=dcc.Graph(id="elbow-curve-graph", config={"displaylogo": False})
                            )
                        ]
                    )
                ]
            ),

            # SECTION 4: PCA DIMENSIONALITY REDUCTION & SECTION 5: MODEL BENCHMARK
            html.Div(style={"marginTop": "24px"}),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(480px, 1fr))", "gap": "20px"},
                children=[
                    create_panel(
                        title="2D Principal Component Analysis (Dimensionality Reduction)",
                        children=[
                            html.P(
                                "Projects criteria pollutant dimensions into a 2D orthogonal subspace while capturing maximum variance, visually separating severe crisis stations from sub-severe stations.",
                                style={"color": "#64748b", "marginBottom": "12px"}
                            ),
                            dcc.Loading(
                                type="circle",
                                children=dcc.Graph(id="pca-2d-graph", config={"displaylogo": False})
                            )
                        ]
                    ),
                    create_panel(
                        title="Machine Learning Models Benchmark Leaderboard",
                        children=[
                            html.P(
                                "Comprehensive benchmark comparison across regression and classification algorithms evaluated on the official Indian test holdout set.",
                                style={"color": "#64748b", "marginBottom": "12px"}
                            ),
                            html.Div(
                                style={"overflowX": "auto"},
                                children=[
                                    html.Table(
                                        style={
                                            "width": "100%",
                                            "borderCollapse": "collapse",
                                            "fontSize": "0.9rem",
                                            "textAlign": "left"
                                        },
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    style={"background": "#f8fafc", "borderBottom": "2px solid #e2e8f0"},
                                                    children=[
                                                        html.Th("Algorithm", style={"padding": "10px"}),
                                                        html.Th("Task Type", style={"padding": "10px"}),
                                                        html.Th("Primary Metric", style={"padding": "10px"}),
                                                        html.Th("Score", style={"padding": "10px"}),
                                                        html.Th("Status", style={"padding": "10px"})
                                                    ]
                                                )
                                            ),
                                            html.Tbody([
                                                html.Tr(
                                                    style={"borderBottom": "1px solid #f1f5f9"},
                                                    children=[
                                                        html.Td(html.B("Linear Regression"), style={"padding": "10px"}),
                                                        html.Td("Continuous AQI", style={"padding": "10px"}),
                                                        html.Td("R² Score / RMSE", style={"padding": "10px"}),
                                                        html.Td("R² = 0.808 (RMSE: 59.3)", style={"padding": "10px", "color": "#2563eb", "fontWeight": "600"}),
                                                        html.Td(html.Span("Baseline", style={"background": "#e2e8f0", "padding": "2px 8px", "borderRadius": "4px", "fontSize": "0.8rem"}))
                                                    ]
                                                ),
                                                html.Tr(
                                                    style={"borderBottom": "1px solid #f1f5f9"},
                                                    children=[
                                                        html.Td(html.B("Logistic Regression"), style={"padding": "10px"}),
                                                        html.Td("Hazard Classification (AQI ≥ 200)", style={"padding": "10px"}),
                                                        html.Td("Accuracy / ROC-AUC", style={"padding": "10px"}),
                                                        html.Td("Acc = 94.5% (AUC: 0.982)", style={"padding": "10px", "color": "#10b981", "fontWeight": "600"}),
                                                        html.Td(html.Span("High Precision", style={"background": "#dcfce7", "color": "#166534", "padding": "2px 8px", "borderRadius": "4px", "fontSize": "0.8rem"}))
                                                    ]
                                                ),
                                                html.Tr(
                                                    style={"borderBottom": "1px solid #f1f5f9"},
                                                    children=[
                                                        html.Td(html.B("K-Nearest Neighbors (KNN)"), style={"padding": "10px"}),
                                                        html.Td("Hazard Classification (AQI ≥ 200)", style={"padding": "10px"}),
                                                        html.Td("Accuracy / F1-Score", style={"padding": "10px"}),
                                                        html.Td("Acc = 94.4% (F1: 0.889)", style={"padding": "10px", "color": "#f59e0b", "fontWeight": "600"}),
                                                        html.Td(html.Span("Instance-Based", style={"background": "#fef3c7", "color": "#92400e", "padding": "2px 8px", "borderRadius": "4px", "fontSize": "0.8rem"}))
                                                    ]
                                                ),
                                                html.Tr(
                                                    style={"borderBottom": "1px solid #f1f5f9", "background": "#f0fdf4"},
                                                    children=[
                                                        html.Td(html.B("Random Forest Regressor"), style={"padding": "10px"}),
                                                        html.Td("Continuous AQI (Production)", style={"padding": "10px"}),
                                                        html.Td("R² Score / RMSE", style={"padding": "10px"}),
                                                        html.Td("R² = 0.907 (RMSE: 41.2)", style={"padding": "10px", "color": "#15803d", "fontWeight": "700"}),
                                                        html.Td(html.Span("⭐ Best Production Model", style={"background": "#bbf7d0", "color": "#14532d", "padding": "2px 8px", "borderRadius": "4px", "fontSize": "0.8rem", "fontWeight": "700"}))
                                                    ]
                                                )
                                            ])
                                        ]
                                    )
                                ]
                            ),
                            html.Div(
                                style={"marginTop": "16px", "padding": "12px", "background": "#f8fafc", "borderRadius": "8px", "border": "1px solid #e2e8f0"},
                                children=[
                                    html.B("Key Machine Learning Takeaway: ", style={"color": "#0f172a"}),
                                    html.Span("The non-linear ensemble Random Forest reduces Root Mean Squared Error from 59.3 (Linear Regression) down to 41.2 (R² = 90.7%), successfully capturing complex photochemical interactions and boundary layer inversions.")
                                ]
                            )
                        ]
                    )
                ]
            ),

            # SECTION 6: CAPSTONE MINI PROJECT - REAL-TIME PREDICTOR & POLICY SIMULATOR
            html.Div(style={"marginTop": "24px"}),
            create_panel(
                title="Real-Time AQI Predictor & Decision Support System",
                children=[
                    html.Div(
                        style={"background": "#eff6ff", "border": "1px solid #bfdbfe", "borderRadius": "8px", "padding": "14px 18px", "marginBottom": "16px"},
                        children=[
                            html.Span("⚡ SYNCHRONIZED WITH GOOGLE COLAB: ", style={"color": "#1d4ed8", "fontWeight": "bold"}),
                            html.Span("This live inference engine uses "),
                            html.Code("models/aqi_model.joblib", style={"background": "#dbeafe", "padding": "2px 6px", "borderRadius": "4px", "color": "#1e40af", "fontWeight": "bold"}),
                            html.Span(" (Random Forest, R² = 0.9072), trained on 29,531 daily records across 26 Indian cities. Select any monitoring station to auto-fill its real telemetry, or adjust pollutant values to simulate environmental policies.")
                        ]
                    ),
                    html.Div(
                        className="form-row",
                        style={"marginBottom": "16px"},
                        children=[
                            html.Label("Load Authentic CPCB Station Telemetry (Preset):", className="form-label", style={"fontWeight": "600", "fontSize": "0.95rem"}),
                            dcc.Dropdown(
                                id="mini-station-select",
                                options=station_options or [],
                                placeholder="Choose any of 419 monitoring stations across India to load real sensor readings...",
                                clearable=True
                            )
                        ]
                    ),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(170px, 1fr))", "gap": "14px", "background": "#f8fafc", "padding": "16px", "borderRadius": "8px", "border": "1px solid #e2e8f0", "marginBottom": "16px"},
                        children=[
                            html.Div([
                                html.Label("PM2.5 (µg/m³):", style={"fontSize": "0.85rem", "fontWeight": "600"}),
                                dcc.Input(id="mini-pm25", type="number", value=65.0, min=0, max=500, step=0.5, className="form-input")
                            ]),
                            html.Div([
                                html.Label("PM10 (µg/m³):", style={"fontSize": "0.85rem", "fontWeight": "600"}),
                                dcc.Input(id="mini-pm10", type="number", value=110.0, min=0, max=600, step=0.5, className="form-input")
                            ]),
                            html.Div([
                                html.Label("NO2 (µg/m³):", style={"fontSize": "0.85rem", "fontWeight": "600"}),
                                dcc.Input(id="mini-no2", type="number", value=35.0, min=0, max=300, step=0.5, className="form-input")
                            ]),
                            html.Div([
                                html.Label("SO2 (µg/m³):", style={"fontSize": "0.85rem", "fontWeight": "600"}),
                                dcc.Input(id="mini-so2", type="number", value=14.0, min=0, max=200, step=0.5, className="form-input")
                            ]),
                            html.Div([
                                html.Label("CO (mg/m³):", style={"fontSize": "0.85rem", "fontWeight": "600"}),
                                dcc.Input(id="mini-co", type="number", value=1.2, min=0, max=50, step=0.1, className="form-input")
                            ]),
                            html.Div([
                                html.Label("O3 (µg/m³):", style={"fontSize": "0.85rem", "fontWeight": "600"}),
                                dcc.Input(id="mini-o3", type="number", value=40.0, min=0, max=250, step=0.5, className="form-input")
                            ]),
                            html.Div([
                                html.Label("Temp (°C):", style={"fontSize": "0.85rem", "fontWeight": "600"}),
                                dcc.Input(id="mini-temp", type="number", value=26.0, min=-5, max=50, step=0.5, className="form-input")
                            ]),
                            html.Div([
                                html.Label("Humidity (%):", style={"fontSize": "0.85rem", "fontWeight": "600"}),
                                dcc.Input(id="mini-humidity", type="number", value=55.0, min=5, max=100, step=1.0, className="form-input")
                            ]),
                            html.Div([
                                html.Label("Wind (km/h):", style={"fontSize": "0.85rem", "fontWeight": "600"}),
                                dcc.Input(id="mini-wind", type="number", value=8.0, min=0, max=40, step=0.5, className="form-input")
                            ])
                        ]
                    ),
                    html.Div(
                        style={"textAlign": "center", "marginBottom": "20px"},
                        children=[
                            html.Button(
                                "🔮 Run Real-Time AQI Prediction (Colab ML Model)",
                                id="mini-predict-btn",
                                n_clicks=0,
                                className="btn btn-primary btn-large",
                                style={"fontSize": "1.05rem", "padding": "12px 28px"}
                            )
                        ]
                    ),
                    dcc.Loading(
                        type="circle",
                        children=html.Div(id="mini-predict-output")
                    )
                ]
            )
        ]
    )
