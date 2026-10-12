"""
Mini Project Callbacks for Dash
Handles interactive analytics, custom CSV/ZIP dataset uploads,
machine learning model updates, and real-time prediction simulator
for the Air Quality Index Mini Project.
"""

import io
import base64
import zipfile
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from dash import Input, Output, State, html

from app.config.logging_config import logger
from app.config.settings import PROJECT_ROOT
from app.dashboard.components.layout import create_metric_card, create_metric_grid
from app.dashboard.components.mini_project_charts import (
    create_aqi_distribution_chart,
    create_category_pie_chart,
    create_pollutant_levels_chart,
    create_city_pollutant_chart,
    create_temporal_trends_chart,
    create_correlation_heatmap,
    train_mini_project_models,
    create_actual_vs_predicted_chart,
    create_pca_variance_chart,
    create_mini_gauge
)


# In-memory storage for datasets and precomputed models
_MINI_DF = None
_DEFAULT_MODELS = None
_UPLOADED_DF = None
_UPLOADED_FILENAME = None
_ACTIVE_MODELS = None


def get_mini_project_df() -> pd.DataFrame:
    """Load the official Mini Project dataset."""
    global _MINI_DF
    if _MINI_DF is not None:
        return _MINI_DF
        
    candidates = [
        PROJECT_ROOT / "mini project final set" / "sample_air_quality_dataset.csv",
        PROJECT_ROOT / "data" / "sample_air_quality_dataset.csv",
        PROJECT_ROOT / "app" / "dashboard" / "assets" / "sample_air_quality_dataset.csv"
    ]
    for p in candidates:
        if p.exists():
            df = pd.read_csv(p)
            _MINI_DF = df
            return _MINI_DF
            
    raise FileNotFoundError("Mini project dataset 'sample_air_quality_dataset.csv' not found.")


def parse_uploaded_contents(contents: str, filename: str) -> pd.DataFrame:
    """Parse base64 uploaded CSV or ZIP file."""
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    if filename.lower().endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(decoded)) as z:
            csv_candidates = [n for n in z.namelist() if n.lower().endswith('.csv') and not n.startswith('__MACOSX')]
            if not csv_candidates:
                raise ValueError("No CSV file found in uploaded ZIP archive.")
            selected_csv = csv_candidates[0]
            for name in csv_candidates:
                if "city_day" in name.lower() or "station_day" in name.lower() or "air_quality" in name.lower():
                    selected_csv = name
                    break
            with z.open(selected_csv) as f:
                raw_bytes = f.read()
            for encoding in ['utf-8', 'latin1', 'utf-8-sig', 'cp1252']:
                try:
                    df = pd.read_csv(io.BytesIO(raw_bytes), encoding=encoding)
                    break
                except Exception:
                    continue
            else:
                raise ValueError(f"Could not decode CSV file ({selected_csv}) inside ZIP archive.")
    else:
        for encoding in ['utf-8', 'latin1', 'utf-8-sig', 'cp1252']:
            try:
                df = pd.read_csv(io.BytesIO(decoded), encoding=encoding)
                break
            except Exception:
                continue
        else:
            raise ValueError("Could not decode CSV file. Please ensure it is valid UTF-8 or Latin-1.")
            
    # Normalize column names to lowercase without special characters
    col_map = {c: str(c).lower().replace(".", "").replace("-", "").strip() for c in df.columns}
    df = df.rename(columns=col_map)
    return df


def get_mini_project_models() -> dict:
    """Get active trained models in memory."""
    global _ACTIVE_MODELS, _DEFAULT_MODELS
    if _ACTIVE_MODELS is not None:
        return _ACTIVE_MODELS
    if _DEFAULT_MODELS is not None:
        _ACTIVE_MODELS = _DEFAULT_MODELS
        return _ACTIVE_MODELS
        
    df = get_mini_project_df()
    _DEFAULT_MODELS = train_mini_project_models(df)
    _ACTIVE_MODELS = _DEFAULT_MODELS
    return _ACTIVE_MODELS


def register_mini_project_callbacks(app):
    """Register all Mini Project callbacks."""
    
    # 1. Dataset Source Toggle
    @app.callback(
        [Output("mini-upload-container", "style"),
         Output("mini-dataset-banner", "children")],
        Input("mini-dataset-source", "value")
    )
    def toggle_dataset_source(source):
        """Toggle file upload dropzone and info banner based on selected dataset."""
        global _UPLOADED_DF, _UPLOADED_FILENAME
        if source == "upload":
            if _UPLOADED_DF is not None:
                banner = f"Active Upload: {_UPLOADED_FILENAME} ({len(_UPLOADED_DF):,} records). Click 'Retrain Models' to train on this dataset."
            else:
                banner = "Please upload your CSV or ZIP dataset file below. The models and visuals will dynamically retrain on your uploaded data."
            return {"display": "block", "marginTop": "12px"}, banner
        else:
            banner = "Active Source: Built-in Mini Project Dataset (3,133 observations across 6 Indian cities). All models and visuals are trained on this data."
            return {"display": "none"}, banner

    # 2. File Upload Handler
    @app.callback(
        Output("mini-upload-status", "children"),
        Input("mini-csv-upload", "contents"),
        State("mini-csv-upload", "filename")
    )
    def handle_upload(contents, filename):
        """Handle uploaded CSV or ZIP file."""
        global _UPLOADED_DF, _UPLOADED_FILENAME
        if not contents or not filename:
            return ""
            
        try:
            df = parse_uploaded_contents(contents, filename)
            _UPLOADED_DF = df
            _UPLOADED_FILENAME = filename
            cols_preview = ", ".join(list(df.columns)[:5])
            if len(df.columns) > 5:
                cols_preview += f" (+{len(df.columns) - 5} more)"
                
            return html.Div([
                html.Div([
                    html.Span("✓ Successfully loaded: ", style={"color": "#16a34a", "fontWeight": "bold"}),
                    html.Span(f"{filename} ({len(df):,} rows, {len(df.columns)} columns)", style={"fontWeight": "600", "color": "#0f172a"})
                ]),
                html.Div(f"Columns: {cols_preview}", style={"fontSize": "0.8rem", "color": "#64748b", "marginTop": "2px"}),
                html.Div("Ready! Click '🚀 Retrain Models on Selected Source' below to evaluate your data.", style={"fontSize": "0.85rem", "color": "#2563eb", "marginTop": "4px", "fontWeight": "500"})
            ], style={"marginTop": "8px", "padding": "10px", "backgroundColor": "#f0fdf4", "borderRadius": "6px", "border": "1px solid #bbf7d0"})
        except Exception as e:
            logger.error(f"Failed to parse uploaded file: {e}")
            return html.Div(f"✗ Failed to read file: {str(e)}", style={"color": "#ef4444", "marginTop": "8px", "fontWeight": "bold", "fontSize": "0.85rem"})

    # 3. EDA Tab Charts
    @app.callback(
        [Output("chart-aqi-dist", "figure"),
         Output("chart-category-pie", "figure"),
         Output("chart-pollutant-means", "figure"),
         Output("chart-city-pollutants", "figure"),
         Output("chart-correlation-heatmap", "figure")],
        Input("mini-project-tabs", "value")
    )
    def render_eda_charts(_):
        """Render all EDA charts for Tab 1."""
        df = get_mini_project_df()
        fig_dist = create_aqi_distribution_chart(df)
        fig_pie = create_category_pie_chart(df)
        fig_means = create_pollutant_levels_chart(df)
        fig_city = create_city_pollutant_chart(df)
        fig_corr = create_correlation_heatmap(df)
        return fig_dist, fig_pie, fig_means, fig_city, fig_corr

    # 4. Temporal Trends Filter
    @app.callback(
        Output("chart-temporal-trend", "figure"),
        Input("mini-trend-city", "value")
    )
    def update_temporal_trend(selected_city):
        """Update temporal trend chart based on selected city filter."""
        df = get_mini_project_df()
        filter_city = None if selected_city == "ALL" else selected_city
        return create_temporal_trends_chart(df, city=filter_city)

    # 5. ML Tab & Model Retraining
    @app.callback(
        [Output("mini-model-comparison-table", "children"),
         Output("chart-actual-vs-pred", "figure"),
         Output("chart-pca-scree", "figure"),
         Output("mini-retrain-status", "children"),
         Output("mini-kpi-cards", "children")],
        [Input("mini-project-tabs", "value"),
         Input("mini-model-select", "value"),
         Input("mini-retrain-btn", "n_clicks")],
        [State("mini-dataset-source", "value")]
    )
    def update_ml_tab(tab_val, selected_model, retrain_clicks, dataset_source):
        """Render ML comparison table, scatter plot, PCA scree plot, and retrain dynamically."""
        global _ACTIVE_MODELS, _UPLOADED_DF, _UPLOADED_FILENAME, _DEFAULT_MODELS
        
        status_msg = ""
        source_label = "Built-in Project Dataset (3,133 records)"
        total_obs = 3133
        cities_count = 6
        
        # Decide which dataset to use
        if dataset_source == "upload":
            if _UPLOADED_DF is not None:
                try:
                    active_df = _UPLOADED_DF
                    _ACTIVE_MODELS = train_mini_project_models(active_df)
                    source_label = f"Uploaded File: {_UPLOADED_FILENAME} ({len(active_df):,} records)"
                    total_obs = len(active_df)
                    cities_count = active_df["city"].nunique() if "city" in active_df.columns else 1
                    status_msg = html.Div([
                        html.Span("✓ Models retrained successfully! ", style={"color": "#16a34a", "fontWeight": "bold"}),
                        html.Span(f"Trained on '{_UPLOADED_FILENAME}' ({total_obs:,} rows) at {datetime.now().strftime('%H:%M:%S')}")
                    ], style={"fontSize": "0.85rem", "marginTop": "6px"})
                except Exception as e:
                    logger.error(f"Error training on uploaded dataset: {e}")
                    status_msg = html.Div(f"✗ Training failed: {str(e)}", style={"color": "#ef4444", "fontWeight": "bold", "fontSize": "0.85rem", "marginTop": "6px"})
                    _ACTIVE_MODELS = get_mini_project_models()
            else:
                status_msg = html.Div("⚠️ Please drag & drop or select a CSV/ZIP file above before retraining.", style={"color": "#f59e0b", "fontWeight": "bold", "fontSize": "0.85rem", "marginTop": "6px"})
                _ACTIVE_MODELS = get_mini_project_models()
        else:
            default_df = get_mini_project_df()
            if _DEFAULT_MODELS is None:
                _DEFAULT_MODELS = train_mini_project_models(default_df)
            _ACTIVE_MODELS = _DEFAULT_MODELS
            total_obs = len(default_df)
            cities_count = default_df["city"].nunique() if "city" in default_df.columns else 6
            if retrain_clicks and retrain_clicks > 0:
                status_msg = html.Div("✓ Reset to Built-in Project Dataset (3,133 records).", style={"color": "#2563eb", "fontWeight": "bold", "fontSize": "0.85rem", "marginTop": "6px"})
                
        models = _ACTIVE_MODELS or get_mini_project_models()
        lr_m = models["lr_metrics"]
        pca_m = models["pca_metrics"]
        rf_m = models["rf_metrics"]
        
        # Build comparison table matching Notebook Step 9
        rows = [
            html.Tr([
                html.Td(html.B("PCA + Linear Regression (Notebook Model)"), style={"padding": "12px"}),
                html.Td(f"{pca_m['mae']:.3f}", style={"padding": "12px"}),
                html.Td(f"{pca_m['mse']:.3f}", style={"padding": "12px"}),
                html.Td(f"{pca_m['rmse']:.3f}", style={"padding": "12px", "fontWeight": "700"}),
                html.Td(f"{pca_m['r2']:.4f}", style={"padding": "12px", "color": "#16a34a", "fontWeight": "700"}),
                html.Td(f"{models['pca_n_components']} Components ({sum(models['pca_variance_ratio']):.1f}% Variance)", style={"padding": "12px", "color": "#2563eb"})
            ], style={"background": "#eff6ff", "borderBottom": "1px solid #bfdbfe"}),
            html.Tr([
                html.Td(html.B("Standard Linear Regression"), style={"padding": "12px"}),
                html.Td(f"{lr_m['mae']:.3f}", style={"padding": "12px"}),
                html.Td(f"{lr_m['mse']:.3f}", style={"padding": "12px"}),
                html.Td(f"{lr_m['rmse']:.3f}", style={"padding": "12px", "fontWeight": "700"}),
                html.Td(f"{lr_m['r2']:.4f}", style={"padding": "12px", "color": "#16a34a", "fontWeight": "700"}),
                html.Td(f"All {len(models['features'])} Features", style={"padding": "12px", "color": "#64748b"})
            ], style={"borderBottom": "1px solid #e2e8f0"}),
            html.Tr([
                html.Td(html.B("Random Forest Regressor (Ensemble Benchmark)"), style={"padding": "12px"}),
                html.Td(f"{rf_m['mae']:.3f}", style={"padding": "12px"}),
                html.Td(f"{rf_m['mse']:.3f}", style={"padding": "12px"}),
                html.Td(f"{rf_m['rmse']:.3f}", style={"padding": "12px", "fontWeight": "700"}),
                html.Td(f"{rf_m['r2']:.4f}", style={"padding": "12px", "color": "#16a34a", "fontWeight": "700"}),
                html.Td("50 Estimators, Non-linear", style={"padding": "12px", "color": "#64748b"})
            ], style={"borderBottom": "1px solid #e2e8f0"})
        ]
        
        table = html.Table(
            style={"width": "100%", "borderCollapse": "collapse", "fontSize": "0.9rem", "backgroundColor": "#ffffff", "borderRadius": "8px", "overflow": "hidden", "boxShadow": "0 1px 3px rgba(0,0,0,0.05)"},
            children=[
                html.Thead(html.Tr([
                    html.Th("Algorithm / Pipeline", style={"padding": "12px", "textAlign": "left"}),
                    html.Th("Mean Absolute Error (MAE)", style={"padding": "12px", "textAlign": "left"}),
                    html.Th("Mean Squared Error (MSE)", style={"padding": "12px", "textAlign": "left"}),
                    html.Th("Root Mean Sq Error (RMSE)", style={"padding": "12px", "textAlign": "left"}),
                    html.Th("R² Score (Variance Explained)", style={"padding": "12px", "textAlign": "left"}),
                    html.Th("Dimensionality / Source", style={"padding": "12px", "textAlign": "left"})
                ], style={"background": "#f8fafc", "borderBottom": "2px solid #cbd5e1"})),
                html.Tbody(rows)
            ]
        )
        
        # Select predictions based on radio button
        y_test = models["y_test"]
        if selected_model == "lr":
            y_pred = models["lr_pred"]
            model_label = "Standard Linear Regression"
        elif selected_model == "rf":
            y_pred = models["rf_pred"]
            model_label = "Random Forest Regressor"
        else:
            y_pred = models["pca_pred"]
            model_label = "PCA (95% Var) + Linear Regression"
            
        fig_scatter = create_actual_vs_predicted_chart(y_test, y_pred, model_name=f"{model_label} ({source_label})")
        fig_scree = create_pca_variance_chart(models["pca_variance_ratio"])
        
        # Update KPI Cards
        pca_r2 = pca_m["r2"] * 100
        cards = [
            create_metric_card("Monitored Observations", f"{total_obs:,} Records", "blue", trend=source_label, icon="📋"),
            create_metric_card("Urban Metropolitan Airsheds", f"{cities_count} Regions", "green", icon="🏙️"),
            create_metric_card("Evaluated Environmental Features", f"{len(models['features'])} Parameters", "purple", icon="🧪"),
            create_metric_card("PCA Model Fidelity (R²)", f"{pca_r2:.1f}% Accuracy", "amber", trend=f"RMSE: {pca_m['rmse']:.2f}", icon="🎯")
        ]
        kpi_grid = create_metric_grid(cards, columns=4)
        
        return table, fig_scatter, fig_scree, status_msg, kpi_grid

    # 6. Live Predictor Simulation
    @app.callback(
        [Output("sim-gauge", "figure"),
         Output("sim-advisory-card", "children")],
        [Input("sim-pm25", "value"),
         Input("sim-pm10", "value"),
         Input("sim-no2", "value"),
         Input("sim-so2", "value"),
         Input("sim-co", "value"),
         Input("sim-o3", "value"),
         Input("sim-temp", "value"),
         Input("sim-humidity", "value"),
         Input("sim-wind", "value")]
    )
    def live_predict_simulation(pm25, pm10, no2, so2, co, o3, temp, humidity, wind):
        """Simulate real-time AQI prediction using the PCA + Linear Regression pipeline."""
        models = get_mini_project_models()
        pipeline = models["pca_pipeline"]
        
        # Build input vector matching active features
        feature_order = models["features"]
        input_data = {
            "pm25": float(pm25 or 45),
            "pm10": float(pm10 or 85),
            "no2": float(no2 or 28),
            "so2": float(so2 or 14),
            "co": float(co or 0.9),
            "o3": float(o3 or 32),
            "temperature": float(temp or 26),
            "humidity": float(humidity or 65),
            "wind_speed": float(wind or 8)
        }
        
        row_vec = [input_data.get(col, 20.0) for col in feature_order]
        X_in = np.array([row_vec])
        
        predicted_aqi = float(pipeline.predict(X_in)[0])
        predicted_aqi = max(0.0, round(predicted_aqi, 1))
        
        # Categorize
        if predicted_aqi <= 50:
            cat, color, advice = "Good", "#10b981", "Air quality is considered satisfactory, and air pollution poses little or no risk. Safe for all outdoor activities."
        elif predicted_aqi <= 100:
            cat, color, advice = "Satisfactory", "#84cc16", "Air quality is acceptable; however, sensitive individuals may experience minor breathing discomfort."
        elif predicted_aqi <= 200:
            cat, color, advice = "Moderate", "#eab308", "Air quality is acceptable for the general public, but members of sensitive groups may experience health effects. Limit prolonged outdoor exertion."
        elif predicted_aqi <= 300:
            cat, color, advice = "Poor", "#f97316", "Everyone may begin to experience health effects; members of sensitive groups may experience more serious health effects. Wear protective masks outdoors."
        elif predicted_aqi <= 400:
            cat, color, advice = "Very Poor", "#ef4444", "Health alert: The risk of health effects is increased for everyone. Avoid outdoor exertion and keep indoor air purified."
        else:
            cat, color, advice = "Severe", "#7f1d1d", "Health emergency warning of emergency conditions: The entire population is more likely to be affected. Stay indoors."
            
        fig_gauge = create_mini_gauge(predicted_aqi, cat, color)
        
        card = html.Div(
            style={
                "borderLeft": f"6px solid {color}",
                "padding": "16px",
                "backgroundColor": "#ffffff",
                "borderRadius": "8px",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.05)"
            },
            children=[
                html.Div([
                    html.Span("Predicted AQI Value: ", style={"color": "#64748b", "fontSize": "0.9rem"}),
                    html.Span(f"{predicted_aqi}", style={"fontWeight": "800", "fontSize": "1.3rem", "color": color, "marginLeft": "6px"})
                ]),
                html.Div([
                    html.Span("Environmental Air Quality: ", style={"color": "#64748b", "fontSize": "0.9rem"}),
                    html.Span(cat, style={"fontWeight": "700", "fontSize": "1.1rem", "color": color, "marginLeft": "6px"})
                ], style={"marginTop": "4px"}),
                html.P(advice, style={"color": "#334155", "marginTop": "10px", "fontSize": "0.9rem", "lineHeight": "1.4"})
            ]
        )
        
        return fig_gauge, card
