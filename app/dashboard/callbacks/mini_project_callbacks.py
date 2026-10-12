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
import dash
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
    create_mini_gauge,
    create_geospatial_map,
    create_location_kpis,
    create_location_ranking_table,
    extract_location_dataframe
)


# In-memory storage for datasets and precomputed models
_MINI_DF = None
_DEFAULT_MODELS = None
_ACTIVE_DF = None
_ACTIVE_FILENAME = None
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


def get_default_models() -> dict:
    """Get or train the default models."""
    global _DEFAULT_MODELS
    if _DEFAULT_MODELS is not None:
        return _DEFAULT_MODELS
    df = get_mini_project_df()
    _DEFAULT_MODELS = train_mini_project_models(df)
    return _DEFAULT_MODELS


def get_active_models() -> dict:
    """Get currently active models."""
    global _ACTIVE_MODELS
    if _ACTIVE_MODELS is not None:
        return _ACTIVE_MODELS
    return get_default_models()


def register_mini_project_callbacks(app):
    """Register all Mini Project callbacks."""

    # 1. EDA Tab Charts
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
        df = _ACTIVE_DF if _ACTIVE_DF is not None else get_mini_project_df()
        fig_dist = create_aqi_distribution_chart(df)
        fig_pie = create_category_pie_chart(df)
        fig_means = create_pollutant_levels_chart(df)
        fig_city = create_city_pollutant_chart(df)
        fig_corr = create_correlation_heatmap(df)
        return fig_dist, fig_pie, fig_means, fig_city, fig_corr

    # 2. Temporal Trends Filter
    @app.callback(
        Output("chart-temporal-trend", "figure"),
        Input("mini-trend-city", "value")
    )
    def update_temporal_trend(selected_city):
        """Update temporal trend chart based on selected city filter."""
        df = _ACTIVE_DF if _ACTIVE_DF is not None else get_mini_project_df()
        filter_city = None if selected_city == "ALL" else selected_city
        return create_temporal_trends_chart(df, city=filter_city)

    # 3. Geospatial Map & Locations Callback
    @app.callback(
        [Output("chart-geospatial-map", "figure"),
         Output("map-kpi-grid", "children"),
         Output("table-location-rankings", "children"),
         Output("map-city-filter", "options")],
        [Input("mini-project-tabs", "value"),
         Input("map-metric-select", "value"),
         Input("map-city-filter", "value"),
         Input("mini-csv-upload", "contents"),
         Input("mini-reset-btn", "n_clicks")]
    )
    def update_geospatial_section(tab_val, selected_metric, selected_city, upload_contents, reset_clicks):
        """Update geospatial map, KPI cards, and station leaderboard table."""
        df = _ACTIVE_DF if _ACTIVE_DF is not None else get_mini_project_df()
        
        # Build city dropdown options from active data
        summary, _ = extract_location_dataframe(df)
        if summary is not None and not summary.empty:
            unique_cities = sorted([str(c) for c in summary["city"].unique()])
            city_options = [{"label": "Pan-India (All Cities)", "value": "ALL"}] + [
                {"label": c, "value": c} for c in unique_cities
            ]
        else:
            city_options = [{"label": "Pan-India (All Cities)", "value": "ALL"}]
            
        fig_map = create_geospatial_map(df, metric=selected_metric or "aqi", selected_city=selected_city)
        kpi_grid = create_location_kpis(df, selected_city=selected_city)
        rankings_table = create_location_ranking_table(df, selected_city=selected_city)
        
        return fig_map, kpi_grid, rankings_table, city_options

    # 4. ML & Visuals Tab: Reactive Upload, Retrain, Model Comparison & Scatter

    @app.callback(
        [Output("mini-model-comparison-table", "children"),
         Output("chart-actual-vs-pred", "figure"),
         Output("chart-pca-scree", "figure"),
         Output("mini-upload-status", "children"),
         Output("mini-dataset-banner", "children"),
         Output("mini-kpi-cards", "children")],
        [Input("mini-project-tabs", "value"),
         Input("mini-model-select", "value"),
         Input("mini-csv-upload", "contents"),
         Input("mini-reset-btn", "n_clicks"),
         Input("mini-retrain-btn", "n_clicks")],
        [State("mini-csv-upload", "filename")]
    )
    def update_ml_tab(tab_val, selected_model, upload_contents, reset_clicks, retrain_clicks, upload_filename):
        """Handle file upload, reset to default, and update ML visualizations dynamically."""
        global _ACTIVE_MODELS, _ACTIVE_DF, _ACTIVE_FILENAME, _DEFAULT_MODELS
        
        triggered = dash.ctx.triggered_id
        
        # 1. Direct file upload
        if triggered == "mini-csv-upload" and upload_contents:
            try:
                df = parse_uploaded_contents(upload_contents, upload_filename)
                _ACTIVE_DF = df
                _ACTIVE_FILENAME = upload_filename
                _ACTIVE_MODELS = train_mini_project_models(df)
                upload_badge = html.Div([
                    html.Span("✓ Successfully loaded & trained on: ", style={"color": "#16a34a", "fontWeight": "bold"}),
                    html.Span(f"{upload_filename} ({len(df):,} rows, {len(df.columns)} columns)!", style={"fontWeight": "600", "color": "#0f172a"})
                ], style={"padding": "8px 12px", "backgroundColor": "#f0fdf4", "border": "1px solid #bbf7d0", "borderRadius": "6px", "fontSize": "0.85rem"})
                banner_text = f"Active Source: Uploaded File '{upload_filename}' ({len(df):,} records). All models and visuals below are evaluated on this data."
            except Exception as e:
                logger.error(f"Failed to parse uploaded dataset: {e}")
                upload_badge = html.Div(f"✗ Failed to read file: {str(e)}", style={"color": "#ef4444", "fontWeight": "bold", "fontSize": "0.85rem"})
                banner_text = "Active Source: Built-in Mini Project Dataset (3,133 observations). (Upload encountered an error)."
                
        # 2. Reset button clicked
        elif triggered == "mini-reset-btn":
            _ACTIVE_DF = None
            _ACTIVE_FILENAME = None
            _ACTIVE_MODELS = get_default_models()
            upload_badge = html.Div("✓ Reset to Built-in Project Dataset (3,133 records).", style={"color": "#2563eb", "fontWeight": "600", "fontSize": "0.85rem"})
            banner_text = "Active Source: Built-in Mini Project Dataset (3,133 observations across 6 Indian cities). All models and visuals are trained on this data."
            
        # 3. Retrain button clicked
        elif triggered == "mini-retrain-btn":
            if _ACTIVE_DF is not None:
                _ACTIVE_MODELS = train_mini_project_models(_ACTIVE_DF)
                upload_badge = html.Div(f"✓ Re-trained models on uploaded file: {_ACTIVE_FILENAME} ({len(_ACTIVE_DF):,} records)", style={"color": "#16a34a", "fontSize": "0.85rem", "fontWeight": "bold"})
                banner_text = f"Active Source: Uploaded File '{_ACTIVE_FILENAME}' ({len(_ACTIVE_DF):,} records)."
            else:
                _ACTIVE_MODELS = get_default_models()
                upload_badge = html.Div("✓ Re-trained models on Built-in Project Dataset (3,133 records).", style={"color": "#2563eb", "fontSize": "0.85rem", "fontWeight": "bold"})
                banner_text = "Active Source: Built-in Mini Project Dataset (3,133 observations across 6 Indian cities)."
                
        # 4. Tab load or model radio switch
        else:
            if _ACTIVE_DF is not None:
                banner_text = f"Active Source: Uploaded File '{_ACTIVE_FILENAME}' ({len(_ACTIVE_DF):,} records). All models and visuals below are evaluated on this data."
                upload_badge = html.Div(f"✓ Using uploaded file: {_ACTIVE_FILENAME} ({len(_ACTIVE_DF):,} records)", style={"color": "#16a34a", "fontSize": "0.85rem", "fontWeight": "500"})
            else:
                banner_text = "Active Source: Built-in Mini Project Dataset (3,133 observations across 6 Indian cities). All models and visuals are trained on this data."
                upload_badge = ""
                
        models = _ACTIVE_MODELS or get_default_models()
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
        source_label = _ACTIVE_FILENAME or "Built-in Dataset"
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
        current_df = _ACTIVE_DF if _ACTIVE_DF is not None else get_mini_project_df()
        total_obs = len(current_df)
        cities_count = current_df["city"].nunique() if "city" in current_df.columns else 1
        pca_r2 = pca_m["r2"] * 100
        
        cards = [
            create_metric_card("Monitored Observations", f"{total_obs:,} Records", "blue", trend=source_label, icon="📋"),
            create_metric_card("Urban Metropolitan Airsheds", f"{cities_count} Regions", "green", icon="🏙️"),
            create_metric_card("Evaluated Environmental Features", f"{len(models['features'])} Parameters", "purple", icon="🧪"),
            create_metric_card("PCA Model Fidelity (R²)", f"{pca_r2:.1f}% Accuracy", "amber", trend=f"RMSE: {pca_m['rmse']:.2f}", icon="🎯")
        ]
        kpi_grid = create_metric_grid(cards, columns=4)
        
        return table, fig_scatter, fig_scree, upload_badge, banner_text, kpi_grid

    # 4. Live Predictor Simulation
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
        """Simulate real-time AQI prediction using the active PCA + Linear Regression pipeline."""
        models = get_active_models()
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
