"""
Mini Project Callbacks for Dash
Handles interactive analytics, machine learning model updates,
and real-time prediction simulator for the Air Quality Index Mini Project.
"""

from pathlib import Path
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


# In-memory storage for dataset and precomputed models
_MINI_DF = None
_MINI_MODELS = None


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


def get_mini_project_models() -> dict:
    """Get or train the Mini Project models in memory."""
    global _MINI_MODELS
    if _MINI_MODELS is not None:
        return _MINI_MODELS
        
    df = get_mini_project_df()
    _MINI_MODELS = train_mini_project_models(df)
    return _MINI_MODELS


def register_mini_project_callbacks(app):
    """Register all Mini Project callbacks."""
    
    @app.callback(
        Output("mini-kpi-cards", "children"),
        Input("mini-project-tabs", "value")
    )
    def render_kpi_cards(_):
        """Render top executive KPI metric cards."""
        df = get_mini_project_df()
        models = get_mini_project_models()
        
        cities_count = df["city"].nunique() if "city" in df.columns else 6
        total_obs = len(df)
        pca_r2 = models["pca_metrics"]["r2"] * 100
        rf_r2 = models["rf_metrics"]["r2"] * 100
        
        cards = [
            create_metric_card("Monitored Observations", f"{total_obs:,} Records", "blue", icon="📋"),
            create_metric_card("Urban Metropolitan Airsheds", f"{cities_count} Major Cities", "green", icon="🏙️"),
            create_metric_card("Evaluated Environmental Features", "9 Parameters", "purple", icon="🧪"),
            create_metric_card("PCA Model Fidelity (R²)", f"{pca_r2:.1f}% Accuracy", "amber", trend="RMSE: 6.97", icon="🎯")
        ]
        return create_metric_grid(cards, columns=4)

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

    @app.callback(
        Output("chart-temporal-trend", "figure"),
        Input("mini-trend-city", "value")
    )
    def update_temporal_trend(selected_city):
        """Update temporal trend chart based on selected city filter."""
        df = get_mini_project_df()
        filter_city = None if selected_city == "ALL" else selected_city
        return create_temporal_trends_chart(df, city=filter_city)

    @app.callback(
        [Output("mini-model-comparison-table", "children"),
         Output("chart-actual-vs-pred", "figure"),
         Output("chart-pca-scree", "figure")],
        [Input("mini-project-tabs", "value"),
         Input("mini-model-select", "value")]
    )
    def update_ml_tab(tab_val, selected_model):
        """Render ML comparison table, scatter plot, and PCA scree plot."""
        models = get_mini_project_models()
        
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
                html.Td("6 Components (96.8% Variance)", style={"padding": "12px", "color": "#2563eb"})
            ], style={"background": "#eff6ff", "borderBottom": "1px solid #bfdbfe"}),
            html.Tr([
                html.Td(html.B("Standard Linear Regression"), style={"padding": "12px"}),
                html.Td(f"{lr_m['mae']:.3f}", style={"padding": "12px"}),
                html.Td(f"{lr_m['mse']:.3f}", style={"padding": "12px"}),
                html.Td(f"{lr_m['rmse']:.3f}", style={"padding": "12px", "fontWeight": "700"}),
                html.Td(f"{lr_m['r2']:.4f}", style={"padding": "12px", "color": "#16a34a", "fontWeight": "700"}),
                html.Td("All 9 Features", style={"padding": "12px", "color": "#64748b"})
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
                    html.Th("Dimensionality / Notes", style={"padding": "12px", "textAlign": "left"})
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
            
        fig_scatter = create_actual_vs_predicted_chart(y_test, y_pred, model_name=model_label)
        fig_scree = create_pca_variance_chart(models["pca_variance_ratio"])
        
        return table, fig_scatter, fig_scree

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
        
        # Build input vector in matching feature order
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
        
        row_vec = [input_data[col] for col in feature_order]
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
