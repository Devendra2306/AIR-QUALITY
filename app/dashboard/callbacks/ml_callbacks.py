"""
Machine Learning Callbacks for Dash
Handles dataset loading, file uploads, model training, visualization updates,
and real-time AQI prediction simulations.
"""

import io
import base64
from datetime import datetime
from typing import Dict, Any, Tuple
import pandas as pd
from dash import Input, Output, State, html, callback_context

from app.config.logging_config import logger
from app.config.settings import PROJECT_ROOT
from app.ml.model_trainer import ml_trainer
from app.ml.aqi_calculator import calculate_overall_aqi, get_aqi_category_info
from app.dashboard.components.layout import create_metric_card, create_metric_grid
from app.dashboard.components.ml_charts import (
    create_actual_vs_predicted_chart,
    create_feature_importance_chart,
    create_residuals_chart,
    create_correlation_heatmap,
    create_confusion_matrix_chart,
    create_aqi_gauge
)


# In-memory storage for uploaded dataset
_UPLOADED_DF = None
_UPLOADED_FILENAME = None


def parse_contents(contents: str, filename: str) -> pd.DataFrame:
    """Parse base64 uploaded CSV or ZIP file."""
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    if filename.lower().endswith(".zip"):
        import zipfile
        with zipfile.ZipFile(io.BytesIO(decoded)) as z:
            csv_candidates = [n for n in z.namelist() if n.lower().endswith('.csv') and not n.startswith('__MACOSX')]
            if not csv_candidates:
                raise ValueError("No CSV file found in uploaded ZIP archive.")
            selected_csv = csv_candidates[0]
            for name in csv_candidates:
                if "city_day" in name.lower() or "station_day" in name.lower():
                    selected_csv = name
                    break
            with z.open(selected_csv) as f:
                raw_bytes = f.read()
            for encoding in ['utf-8', 'latin1', 'utf-8-sig', 'cp1252']:
                try:
                    df = pd.read_csv(io.BytesIO(raw_bytes), encoding=encoding)
                    return df
                except Exception:
                    continue
            raise ValueError(f"Could not decode CSV file ({selected_csv}) inside ZIP archive.")
    else:
        for encoding in ['utf-8', 'latin1', 'utf-8-sig', 'cp1252']:
            try:
                df = pd.read_csv(io.BytesIO(decoded), encoding=encoding)
                return df
            except Exception:
                continue
        raise ValueError("Could not decode CSV file. Please ensure it is valid UTF-8 or Latin-1.")


def register_ml_callbacks(app):
    """Register all ML related callbacks."""
    
    @app.callback(
        [Output("ml-upload-container", "style"),
         Output("ml-dataset-info-banner", "children")],
        Input("ml-dataset-source", "value")
    )
    def toggle_dataset_source(source):
        """Toggle file upload dropzone and info banner based on selected dataset."""
        global _UPLOADED_DF, _UPLOADED_FILENAME
        if source == "upload":
            if _UPLOADED_DF is not None:
                banner = f"Active Upload: {_UPLOADED_FILENAME} ({len(_UPLOADED_DF):,} rows, {len(_UPLOADED_DF.columns)} columns). Click 'Train Model' to train on this dataset."
            else:
                banner = "Please upload your CSV or ZIP dataset file below. The model will automatically parse and use it for training."
            return {"display": "block", "marginTop": "12px"}, banner
        elif source == "database":
            banner = "Connecting directly to local DuckDB analytical database (raw.measurements table)."
            return {"display": "none"}, banner
        else:
            banner = "Active: Official Indian National Air Quality Dataset (29,531 daily records across 26 major cities)."
            return {"display": "none"}, banner

    @app.callback(
        Output("ml-upload-status", "children"),
        Input("ml-csv-upload", "contents"),
        State("ml-csv-upload", "filename")
    )
    def handle_upload(contents, filename):
        """Handle uploaded CSV or ZIP file."""
        global _UPLOADED_DF, _UPLOADED_FILENAME
        if not contents or not filename:
            return ""
            
        try:
            df = parse_contents(contents, filename)
            _UPLOADED_DF = df
            _UPLOADED_FILENAME = filename
            cols_preview = ", ".join(list(df.columns)[:5])
            if len(df.columns) > 5:
                cols_preview += f" (+{len(df.columns) - 5} more)"
            return html.Div([
                html.Div([
                    html.Span("✓ Successfully loaded: ", style={"color": "#10b981", "fontWeight": "bold"}),
                    html.Span(f"{filename} ({len(df):,} rows, {len(df.columns)} columns)", style={"fontWeight": "600", "color": "#0f172a"})
                ]),
                html.Div(f"Columns: {cols_preview}", style={"fontSize": "0.8rem", "color": "#64748b", "marginTop": "2px"}),
                html.Div("Ready! Select your target variable and click '🚀 Train Model & Generate Visuals'.", style={"fontSize": "0.85rem", "color": "#2563eb", "marginTop": "4px", "fontWeight": "500"})
            ], style={"marginTop": "8px", "padding": "8px", "backgroundColor": "#f0fdf4", "borderRadius": "6px", "border": "1px solid #bbf7d0"})
        except Exception as e:
            logger.error(f"Failed to parse uploaded file: {e}")
            return html.Div(f"✗ Failed to read file: {str(e)}", style={"color": "#ef4444", "marginTop": "8px", "fontWeight": "bold"})

    @app.callback(
        [Output("ml-metrics-container", "children"),
         Output("ml-chart-actual-vs-pred", "figure"),
         Output("ml-chart-feature-importance", "figure"),
         Output("ml-chart-residuals", "figure"),
         Output("ml-chart-correlation", "figure"),
         Output("ml-training-status", "children")],
        [Input("ml-train-btn", "n_clicks")],
        [State("ml-dataset-source", "value"),
         State("ml-target-column", "value"),
         State("ml-algorithm", "value"),
         State("ml-test-split", "value")]
    )
    def train_and_visualize(n_clicks, dataset_source, target_column, algorithm, test_split):
        """Train model and update all visual analytics."""
        global _UPLOADED_DF, _UPLOADED_FILENAME
        from app.dashboard.components.charts import create_empty_figure
        
        test_ratio = float(test_split) / 100.0 if test_split else 0.2
        task_type = "classification" if target_column == "aqi_category" else "regression"
        
        try:
            # 1. Load Data
            if dataset_source == "upload":
                if _UPLOADED_DF is not None:
                    df = _UPLOADED_DF.copy()
                    source_name = f"Uploaded File: {_UPLOADED_FILENAME}"
                else:
                    return (
                        html.Div(),
                        create_empty_figure("No file uploaded. Please upload a CSV or ZIP dataset file above."),
                        create_empty_figure("No file uploaded"),
                        create_empty_figure("No file uploaded"),
                        create_empty_figure("No file uploaded"),
                        html.Div("⚠️ Please upload a CSV or ZIP dataset first before training.", style={"color": "#f59e0b", "marginTop": "10px", "fontWeight": "bold"})
                    )
            elif dataset_source == "database":
                df = ml_trainer.load_from_database()
                source_name = "DuckDB Analytical Database"
            else:
                # "cpcb_national"
                national_path = PROJECT_ROOT / "data" / "city_day.csv"
                if national_path.exists():
                    df = pd.read_csv(national_path)
                    source_name = "Indian National Dataset (29,531 records)"
                else:
                    sample_path = PROJECT_ROOT / "data" / "sample_air_quality_dataset.csv"
                    df = pd.read_csv(sample_path)
                    source_name = "Sample Dataset"
            
            # Enrich dataframe with AQI calculation if columns match
            from app.ml.aqi_calculator import enrich_dataframe_with_aqi
            df = enrich_dataframe_with_aqi(df)
                    
            # 2. Train model
            results = ml_trainer.train(
                df=df,
                target_column=target_column,
                algorithm=algorithm,
                task_type=task_type,
                test_size=test_ratio
            )
            
            metrics = results["metrics"]
            visual_data = results["visual_data"]
            total_records = metrics.get('train_samples', 0) + metrics.get('test_samples', 0)
            
            # 3. Create Metric Cards
            if task_type == "regression":
                metric_cards = [
                    create_metric_card("R² Score (Accuracy)", f"{metrics.get('r2_score', 0):.4f}", "green"),
                    create_metric_card("Mean Absolute Error (MAE)", f"{metrics.get('mae', 0):.2f}", "blue"),
                    create_metric_card("Root Mean Sq Error (RMSE)", f"{metrics.get('rmse', 0):.2f}", "amber"),
                    create_metric_card("Dataset Used", f"{total_records:,} records", "purple", trend=source_name)
                ]
            else:
                metric_cards = [
                    create_metric_card("Accuracy Score", f"{metrics.get('accuracy', 0)*100:.1f}%", "green"),
                    create_metric_card("Precision (Weighted)", f"{metrics.get('precision', 0):.3f}", "blue"),
                    create_metric_card("F1-Score (Macro)", f"{metrics.get('f1_score', 0):.3f}", "amber"),
                    create_metric_card("Dataset Used", f"{total_records:,} records", "purple", trend=source_name)
                ]
            metrics_grid = create_metric_grid(metric_cards, columns=4)
            
            # 4. Generate Interactive Plots
            if task_type == "regression":
                chart_pred = create_actual_vs_predicted_chart(
                    visual_data.get("actual_vs_pred", []),
                    title=f"Actual vs. Predicted {target_column.upper()} ({source_name})"
                )
                chart_res = create_residuals_chart(
                    visual_data.get("residuals", []),
                    title=f"Residual Error Distribution ({algorithm.replace('_', ' ').title()})"
                )
            else:
                chart_pred = create_confusion_matrix_chart(
                    visual_data.get("confusion_matrix", {}),
                    title=f"Confusion Matrix ({source_name})"
                )
                chart_res = create_residuals_chart([], title="Residuals not applicable for classification")
                
            chart_feat = create_feature_importance_chart(
                visual_data.get("feature_importance", []),
                title=f"Feature Importance ({algorithm.replace('_', ' ').title()})"
            )
            
            chart_corr = create_correlation_heatmap(
                visual_data.get("correlation_matrix", {}),
                title="Inter-Pollutant Correlation Heatmap"
            )
            
            status_text = html.Div([
                html.Span("✓ Model trained successfully! ", style={"color": "#10b981", "fontWeight": "bold"}),
                html.Span(f"Algorithm: {algorithm.replace('_', ' ').title()} | Target: {target_column.upper()} | Trained on: {source_name} ({total_records:,} samples) | Finished at {datetime.now().strftime('%H:%M:%S')}")
            ], style={"marginTop": "10px", "fontSize": "0.95rem"})
            
            return metrics_grid, chart_pred, chart_feat, chart_res, chart_corr, status_text
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            empty_fig = create_empty_figure(f"Training Error: {str(e)}")
            err_msg = html.Div(f"✗ Error during training: {str(e)}", style={"color": "#ef4444", "marginTop": "10px", "fontWeight": "bold"})
            return html.Div(), empty_fig, empty_fig, empty_fig, empty_fig, err_msg

    @app.callback(
        [Output("sim-gauge-chart", "figure"),
         Output("sim-advice-card", "children")],
        [Input("sim-predict-btn", "n_clicks"),
         Input("ml-train-btn", "n_clicks")],
        [State("sim-pm25", "value"),
         State("sim-pm10", "value"),
         State("sim-no2", "value"),
         State("sim-so2", "value"),
         State("sim-co", "value"),
         State("sim-o3", "value"),
         State("sim-temp", "value"),
         State("sim-humidity", "value"),
         State("sim-wind", "value")]
    )
    def live_predict(sim_clicks, train_clicks, pm25, pm10, no2, so2, co, o3, temp, humidity, wind):
        """Compute live prediction from current input values."""
        input_dict = {
            "pm25": float(pm25 or 45.0),
            "pm10": float(pm10 or 85.0),
            "no2": float(no2 or 28.0),
            "so2": float(so2 or 14.0),
            "co": float(co or 0.9),
            "o3": float(o3 or 32.0),
            "temperature": float(temp or 26.5),
            "humidity": float(humidity or 65.0),
            "wind_speed": float(wind or 8.5)
        }
        
        try:
            # Predict using ML model if available
            pred_res = ml_trainer.predict_single(input_dict)
            val = pred_res["predicted_value"]
            cat = pred_res["category"]
            color = pred_res["color"]
            advice = pred_res["advice"]
        except Exception:
            # Fallback to direct EPA / NAQI formula
            val, dom, cat, color = calculate_overall_aqi(input_dict)
            advice_info = get_aqi_category_info(val)
            advice = advice_info["advice"]
            
        gauge_fig = create_aqi_gauge(val if isinstance(val, (int, float)) else 100, cat, color)
        
        advice_card = html.Div(
            className="advice-card-inner",
            style={"borderLeft": f"6px solid {color}", "padding": "16px", "backgroundColor": "#ffffff", "borderRadius": "8px", "boxShadow": "0 2px 4px rgba(0,0,0,0.05)"},
            children=[
                html.Div([
                    html.Span(f"Air Quality Status: ", style={"color": "#64748b", "fontSize": "0.9rem"}),
                    html.Span(cat, style={"color": color, "fontWeight": "bold", "fontSize": "1.2rem", "marginLeft": "6px"})
                ]),
                html.Div([
                    html.Span("Predicted AQI Value: ", style={"color": "#64748b", "fontSize": "0.9rem"}),
                    html.Span(f"{val}", style={"fontWeight": "bold", "fontSize": "1.1rem", "color": "#0f172a", "marginLeft": "6px"})
                ], style={"marginTop": "6px"}),
                html.P(advice, style={"color": "#334155", "marginTop": "10px", "fontSize": "0.95rem", "lineHeight": "1.4"})
            ]
        )
        
        return gauge_fig, advice_card
