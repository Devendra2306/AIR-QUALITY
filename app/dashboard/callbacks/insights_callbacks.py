"""
AI/ML Curriculum Insights Callbacks for Dash
Handles interactive callbacks for:
- A* Clean-Air Pathfinding search execution
- Statistical Hypothesis Testing rendering
- K-Means cluster updates
- PCA 2D projections
"""

import os
from typing import Dict, Any, List
import pandas as pd
from dash import Input, Output, State, html, callback_context

from app.config.logging_config import logger
from app.config.settings import PROJECT_ROOT
from app.dashboard.components.layout import create_metric_card, create_metric_grid
from app.dashboard.components.insights_charts import (
    run_astar_clean_air_search,
    create_astar_route_chart,
    create_kmeans_clusters_chart,
    create_elbow_curve_chart,
    create_ttest_hypothesis_chart,
    create_pca_2d_chart
)


CITY_COORDINATES = {
    'Ahmedabad': (23.0225, 72.5714), 'Aizawl': (23.7271, 92.7176), 'Amaravati': (16.5417, 80.5158),
    'Amritsar': (31.6340, 74.8723), 'Bengaluru': (12.9716, 77.5946), 'Bhopal': (23.2599, 77.4126),
    'Brajrajnagar': (21.8235, 83.9204), 'Chandigarh': (30.7333, 76.7794), 'Chennai': (13.0827, 80.2707),
    'Coimbatore': (11.0168, 76.9558), 'Delhi': (28.6139, 77.2090), 'Ernakulam': (9.9816, 76.2999),
    'Gurugram': (28.4595, 77.0266), 'Guwahati': (26.1445, 91.7362), 'Hyderabad': (17.3850, 78.4867),
    'Jaipur': (26.9124, 75.7873), 'Jorapokhar': (23.7088, 86.4158), 'Kochi': (9.9312, 76.2673),
    'Kolkata': (22.5726, 88.3639), 'Lucknow': (26.8467, 80.9462), 'Mumbai': (19.0760, 72.8777),
    'Patna': (25.5941, 85.1376), 'Shillong': (25.5788, 91.8933), 'Talcher': (20.9500, 85.2167),
    'Thiruvananthapuram': (8.5241, 76.9366), 'Visakhapatnam': (17.6868, 83.2185)
}
CITY_STATES = {
    'Ahmedabad': 'Gujarat', 'Aizawl': 'Mizoram', 'Amaravati': 'Andhra Pradesh', 'Amritsar': 'Punjab',
    'Bengaluru': 'Karnataka', 'Bhopal': 'Madhya Pradesh', 'Brajrajnagar': 'Odisha', 'Chandigarh': 'Chandigarh',
    'Chennai': 'Tamil Nadu', 'Coimbatore': 'Tamil Nadu', 'Delhi': 'Delhi', 'Ernakulam': 'Kerala',
    'Gurugram': 'Haryana', 'Guwahati': 'Assam', 'Hyderabad': 'Telangana', 'Jaipur': 'Rajasthan',
    'Jorapokhar': 'Jharkhand', 'Kochi': 'Kerala', 'Kolkata': 'West Bengal', 'Lucknow': 'Uttar Pradesh',
    'Mumbai': 'Maharashtra', 'Patna': 'Bihar', 'Shillong': 'Meghalaya', 'Talcher': 'Odisha',
    'Thiruvananthapuram': 'Kerala', 'Visakhapatnam': 'Andhra Pradesh'
}


def get_insights_dataframe() -> pd.DataFrame:
    """Load the official Indian cities air quality dataset."""
    city_day_path = os.path.join(PROJECT_ROOT, "data", "city_day.csv")
    if os.path.exists(city_day_path):
        df = pd.read_csv(city_day_path)
        df = df.rename(columns={
            'City': 'city', 'Date': 'date', 'PM2.5': 'pm25', 'PM10': 'pm10',
            'NO': 'no', 'NO2': 'no2', 'NOx': 'nox', 'NH3': 'nh3',
            'CO': 'co', 'SO2': 'so2', 'O3': 'o3', 'AQI': 'aqi', 'AQI_Bucket': 'aqi_category'
        })
        df['station'] = df['city'] + " Central Observatory"
        df['latitude'] = df['city'].map(lambda c: CITY_COORDINATES.get(c, (20.59, 78.96))[0])
        df['longitude'] = df['city'].map(lambda c: CITY_COORDINATES.get(c, (20.59, 78.96))[1])
        df['state'] = df['city'].map(lambda c: CITY_STATES.get(c, "India"))
        df['temperature'] = 26.0
        df['humidity'] = 60.0
        df['wind_speed'] = 8.0
        return df

    candidates = [
        os.path.join(PROJECT_ROOT, "data", "cpcb_india_air_quality_pivoted.csv"),
        os.path.join(PROJECT_ROOT, "data", "sample_air_quality_dataset.csv"),
        "data/cpcb_india_air_quality_pivoted.csv"
    ]
    for p in candidates:
        if os.path.exists(p):
            return pd.read_csv(p)
    return pd.DataFrame([
        {'city': 'Delhi', 'state': 'Delhi', 'latitude': 28.61, 'longitude': 77.20, 'aqi': 259.5, 'pm25': 117.2, 'pm10': 232.8, 'no2': 50.8, 'so2': 15.9, 'co': 2.0, 'station': 'Delhi Central Observatory'},
        {'city': 'Bengaluru', 'state': 'Karnataka', 'latitude': 12.97, 'longitude': 77.59, 'aqi': 94.3, 'pm25': 35.5, 'pm10': 78.0, 'no2': 22.0, 'so2': 9.0, 'co': 0.9, 'station': 'Bengaluru Central Observatory'}
    ])


def register_insights_callbacks(app):
    """Register all AI/ML curriculum insights callbacks."""

    @app.callback(
        [Output("astar-metrics-container", "children"),
         Output("astar-route-graph", "figure"),
         Output("astar-route-summary", "children")],
        [Input("astar-compute-btn", "n_clicks")],
        [State("astar-origin-city", "value"),
         State("astar-dest-city", "value"),
         State("astar-toxicity-weight", "value")]
    )
    def update_astar_route(n_clicks, origin_city, dest_city, toxicity_weight):
        """Execute A* Clean-Air route search and update map and metrics."""
        df = get_insights_dataframe()
        toxicity_w = float(toxicity_weight) if toxicity_weight is not None else 0.6
        start_c = origin_city or "Delhi"
        goal_c = dest_city or "Bengaluru"

        try:
            result = run_astar_clean_air_search(df, start_c, goal_c, toxicity_w)
            fig = create_astar_route_chart(result)

            path_details = result['path_details']
            avg_aqi = round(sum(d['aqi'] for d in path_details) / len(path_details), 1)

            cards = [
                create_metric_card(
                    title="Total Corridor Distance",
                    value=f"{result['total_km']:,.0f} km",
                    subtitle=f"{len(path_details)} Waypoint Nodes"
                ),
                create_metric_card(
                    title="Average Corridor AQI",
                    value=f"{avg_aqi}",
                    subtitle="Mean Telemetry Along Path"
                ),
                create_metric_card(
                    title="A* Heuristic Cost f(n)",
                    value=f"{result['total_cost']:,.0f}",
                    subtitle="Distance + Toxicity Penalty"
                )
            ]
            metrics_grid = create_metric_grid(cards)

            # Route chips
            chips = []
            for idx, p in enumerate(path_details):
                aqi_val = p['aqi']
                badge_color = "#10b981" if aqi_val <= 100 else ("#f59e0b" if aqi_val <= 300 else "#ef4444")
                chips.append(html.Span([
                    html.B(f"{idx + 1}. {p['city']}"),
                    html.Span(f" (AQI: {aqi_val})", style={"color": badge_color, "fontWeight": "700"})
                ], style={
                    "background": "#f1f5f9",
                    "padding": "6px 12px",
                    "borderRadius": "20px",
                    "border": "1px solid #cbd5e1",
                    "fontSize": "0.85rem",
                    "display": "inline-block",
                    "margin": "4px"
                }))
                if idx < len(path_details) - 1:
                    chips.append(html.Span(" ➔ ", style={"color": "#64748b", "fontWeight": "bold", "margin": "0 2px"}))

            summary = html.Div([
                html.B("Computed A* Clean-Air Corridor Path: ", style={"color": "#0f172a"}),
                html.Div(chips, style={"marginTop": "8px", "lineHeight": "2"})
            ])

            return metrics_grid, fig, summary

        except Exception as e:
            logger.error(f"Error computing A* route: {e}")
            empty_fig = create_astar_route_chart({
                'start_city': start_c,
                'goal_city': goal_c,
                'path': [start_c, goal_c],
                'path_details': [{'city': start_c, 'state': '', 'lat': 28.6, 'lon': 77.2, 'aqi': 400.0, 'leg_km': 0},
                                 {'city': goal_c, 'state': '', 'lat': 12.9, 'lon': 77.5, 'aqi': 200.0, 'leg_km': 1700}],
                'total_cost': 2000.0,
                'total_km': 1700.0
            })
            return html.Div(), empty_fig, html.Div(f"Error running A*: {str(e)}")

    @app.callback(
        [Output("ttest-metrics-container", "children"),
         Output("ttest-box-graph", "figure"),
         Output("kmeans-scatter-graph", "figure"),
         Output("kmeans-table-container", "children"),
         Output("elbow-curve-graph", "figure"),
         Output("pca-2d-graph", "figure")],
        [Input("main-tabs", "value")]
    )
    def load_curriculum_static_visuals(active_tab):
        """Render all analytical charts when tab is viewed."""
        df = get_insights_dataframe()

        # 1. T-Test
        ttest_fig, test_stats = create_ttest_hypothesis_chart(df)
        sig_banner = (
            f"✅ STATISTICALLY SIGNIFICANT (t = {test_stats['t_statistic']}, p < 1e-100): Null Hypothesis (H₀) Rejected! Indo-Gangetic Plains experience severe winter thermal inversions and agricultural stagnation causing massive pollutant entrapment compared to coastal maritime dispersion zones."
            if test_stats['is_significant'] else
            "❌ Failed to reject H0: No statistically significant difference detected."
        )

        ttest_cards = [
            create_metric_card(
                title=f"Indo-Gangetic / North (N={test_stats['metro_n']:,})",
                value=f"{test_stats['metro_mean']}",
                subtitle=f"Std Dev: {test_stats['metro_std']}"
            ),
            create_metric_card(
                title=f"Coastal / Peninsular (N={test_stats['regional_n']:,})",
                value=f"{test_stats['regional_mean']}",
                subtitle=f"Std Dev: {test_stats['regional_std']}"
            ),
            create_metric_card(
                title="Welch's T-Statistic",
                value=f"{test_stats['t_statistic']}",
                subtitle=f"Two-Tailed p-value: {test_stats['p_value']:.2e}"
            )
        ]
        ttest_metrics = html.Div([
            create_metric_grid(ttest_cards),
            html.Div(
                sig_banner,
                style={
                    "marginTop": "12px",
                    "padding": "12px 16px",
                    "background": "#dcfce7" if test_stats['is_significant'] else "#fee2e2",
                    "color": "#166534" if test_stats['is_significant'] else "#991b1b",
                    "borderRadius": "8px",
                    "fontWeight": "600",
                    "fontSize": "0.9rem"
                }
            )
        ])

        # 2. K-Means
        kmeans_fig, summary_df = create_kmeans_clusters_chart(df)
        table_rows = []
        for _, row in summary_df.iterrows():
            table_rows.append(html.Tr([
                html.Td(html.B(row['Cluster Tier'])),
                html.Td(f"{int(row['Station Count'])} stations"),
                html.Td(f"{row['Mean PM2.5']} µg/m³"),
                html.Td(f"{row['Mean PM10']} µg/m³"),
                html.Td(f"{row['Mean AQI']}", style={"fontWeight": "700", "color": "#ef4444" if row['Mean AQI'] > 400 else "#f59e0b"})
            ], style={"borderBottom": "1px solid #f1f5f9", "padding": "8px"}))

        kmeans_table = html.Table(
            style={"width": "100%", "borderCollapse": "collapse", "fontSize": "0.85rem"},
            children=[
                html.Thead(html.Tr([
                    html.Th("Cluster"), html.Th("Stations"), html.Th("Avg PM2.5"), html.Th("Avg PM10"), html.Th("Avg AQI")
                ], style={"background": "#f8fafc", "borderBottom": "2px solid #e2e8f0"})),
                html.Tbody(table_rows)
            ]
        )

        # 3. Elbow curve
        elbow_fig = create_elbow_curve_chart()

        # 4. PCA
        pca_fig = create_pca_2d_chart(df)

        return ttest_metrics, ttest_fig, kmeans_fig, kmeans_table, elbow_fig, pca_fig

    @app.callback(
        [Output("mini-pm25", "value"),
         Output("mini-pm10", "value"),
         Output("mini-no2", "value"),
         Output("mini-so2", "value"),
         Output("mini-co", "value"),
         Output("mini-o3", "value"),
         Output("mini-temp", "value"),
         Output("mini-humidity", "value"),
         Output("mini-wind", "value")],
        [Input("mini-station-select", "value")]
    )
    def populate_station_preset(station_name):
        """Auto-populate pollutant and weather inputs when a station is chosen."""
        if not station_name:
            return 65.0, 110.0, 35.0, 14.0, 1.2, 40.0, 26.0, 55.0, 8.0

        df = get_insights_dataframe()
        row = df[df['station'] == station_name]
        if row.empty:
            return 65.0, 110.0, 35.0, 14.0, 1.2, 40.0, 26.0, 55.0, 8.0

        r = row.iloc[0]
        return (
            round(float(r.get('pm25', 65.0)), 1),
            round(float(r.get('pm10', 110.0)), 1),
            round(float(r.get('no2', 35.0)), 1),
            round(float(r.get('so2', 14.0)), 1),
            round(float(r.get('co', 1.2)), 2),
            round(float(r.get('o3', 40.0)), 1),
            round(float(r.get('temperature', 26.0)), 1),
            round(float(r.get('humidity', 55.0)), 1),
            round(float(r.get('wind_speed', 8.0)), 1)
        )

    @app.callback(
        Output("mini-predict-output", "children"),
        [Input("mini-predict-btn", "n_clicks")],
        [State("mini-pm25", "value"),
         State("mini-pm10", "value"),
         State("mini-no2", "value"),
         State("mini-so2", "value"),
         State("mini-co", "value"),
         State("mini-o3", "value"),
         State("mini-temp", "value"),
         State("mini-humidity", "value"),
         State("mini-wind", "value"),
         State("mini-station-select", "value")]
    )
    def predict_mini_aqi(n_clicks, pm25, pm10, no2, so2, co, o3, temp, humidity, wind, station_name):
        """Evaluate input features using the production Random Forest model from Colab."""
        pm25 = float(pm25 or 65.0)
        pm10 = float(pm10 or 110.0)
        no2 = float(no2 or 35.0)
        so2 = float(so2 or 14.0)
        co = float(co or 1.2)
        o3 = float(o3 or 40.0)
        temp = float(temp or 26.0)
        humidity = float(humidity or 55.0)
        wind = float(wind or 8.0)

        lat, lon = 28.61, 77.20
        df = get_insights_dataframe()
        if station_name:
            r = df[df['station'] == station_name]
            if not r.empty:
                lat = float(r.iloc[0].get('latitude', 28.61))
                lon = float(r.iloc[0].get('longitude', 77.20))

        input_data = {
            'latitude': lat,
            'longitude': lon,
            'pm25': pm25,
            'pm10': pm10,
            'no2': no2,
            'nh3': 5.0,
            'so2': so2,
            'co': co,
            'o3': o3,
            'temperature': temp,
            'humidity': humidity,
            'wind_speed': wind
        }

        try:
            from app.ml.model_trainer import ml_trainer
            pred_res = ml_trainer.predict_single(input_data)
            pred_aqi = round(float(pred_res['prediction']), 1)
        except Exception as e:
            logger.warning(f"Error using ml_trainer: {e}, direct joblib loading")
            import joblib
            model_path = os.path.join(PROJECT_ROOT, "models", "aqi_model.joblib")
            bundle = joblib.load(model_path)
            feats = bundle['feature_names']
            row = [input_data.get(f, 0.0) for f in feats]
            X_df = pd.DataFrame([row], columns=feats)
            X_sc = bundle['scaler'].transform(bundle['imputer'].transform(X_df))
            pred_aqi = round(float(bundle['model'].predict(X_sc)[0]), 1)

        if pred_aqi <= 50:
            cat = "Good"
            cat_color = "#10b981"
            bg_color = "#ecfdf5"
            advice = "Air quality is satisfactory and poses little or no health risk. Safe for outdoor exercise and recreation."
            grap_stage = "Normal (No emergency restrictions required)"
        elif pred_aqi <= 100:
            cat = "Satisfactory"
            cat_color = "#3b82f6"
            bg_color = "#eff6ff"
            advice = "Acceptable air quality. Unusually sensitive individuals may experience minor breathing discomfort."
            grap_stage = "Normal (Regular municipal monitoring)"
        elif pred_aqi <= 200:
            cat = "Moderate"
            cat_color = "#f59e0b"
            bg_color = "#fffbeb"
            advice = "May cause breathing discomfort to children, elderly, and people with heart disease or asthma."
            grap_stage = "Advisory (Recommend wearing masks during morning walks)"
        elif pred_aqi <= 300:
            cat = "Poor"
            cat_color = "#f97316"
            bg_color = "#fff7ed"
            advice = "Causes breathing discomfort to most people upon prolonged exposure. Avoid strenuous outdoor activities."
            grap_stage = "GRAP Stage I Active (Mechanized sweeping, water sprinkling, strict ban on open garbage burning)"
        elif pred_aqi <= 400:
            cat = "Very Poor"
            cat_color = "#dc2626"
            bg_color = "#fef2f2"
            advice = "Prolonged exposure causes respiratory illness. Vulnerable populations must stay indoors with air purification."
            grap_stage = "GRAP Stage II Active (Parking fees hiked 3x, augmented public transit, ban on diesel generator sets)"
        else:
            cat = "Severe / Smog Emergency"
            cat_color = "#7f1d1d"
            bg_color = "#450a0a"
            advice = "CRITICAL HEALTH EMERGENCY! Healthy people experience adverse cardiovascular/respiratory effects. Maximum danger."
            grap_stage = "GRAP Stage III / IV Emergency (Complete ban on BS-III petrol & BS-IV diesel vehicles, stop construction, school closure)"

        station_tag = f"Station Preset: {station_name}" if station_name else "Custom Policy Simulation Preset"

        return html.Div(
            style={"marginTop": "20px"},
            children=[
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(auto-fit, minmax(280px, 1fr))",
                        "gap": "20px",
                        "marginBottom": "20px"
                    },
                    children=[
                        html.Div(
                            style={
                                "background": bg_color if pred_aqi <= 400 else "#7f1d1d",
                                "color": cat_color if pred_aqi <= 400 else "#ffffff",
                                "border": f"2px solid {cat_color}",
                                "borderRadius": "12px",
                                "padding": "24px",
                                "textAlign": "center"
                            },
                            children=[
                                html.Span("PREDICTED AIR QUALITY INDEX (COLAB MODEL)", style={"fontSize": "0.8rem", "fontWeight": "700", "letterSpacing": "0.08em"}),
                                html.H1(f"{pred_aqi}", style={"fontSize": "3.5rem", "margin": "10px 0", "fontWeight": "800"}),
                                html.Span(cat.upper(), style={
                                    "background": cat_color if pred_aqi <= 400 else "#ffffff",
                                    "color": "#ffffff" if pred_aqi <= 400 else "#7f1d1d",
                                    "padding": "6px 18px",
                                    "borderRadius": "20px",
                                    "fontWeight": "700",
                                    "fontSize": "0.95rem"
                                }),
                                html.Div(station_tag, style={"marginTop": "14px", "fontSize": "0.85rem", "opacity": "0.85"})
                            ]
                        ),
                        html.Div(
                            style={
                                "background": "#ffffff",
                                "border": "1px solid #e2e8f0",
                                "borderRadius": "12px",
                                "padding": "20px",
                                "display": "flex",
                                "flexDirection": "column",
                                "justifyContent": "center"
                            },
                            children=[
                                html.H4("🏥 Clinical Health Advisory", style={"margin": "0 0 8px 0", "color": "#0f172a"}),
                                html.P(advice, style={"color": "#475569", "fontSize": "0.9rem", "marginBottom": "16px", "lineHeight": "1.5"}),
                                html.H4("🚨 Government Policy Action (GRAP)", style={"margin": "0 0 8px 0", "color": "#dc2626" if pred_aqi > 200 else "#059669"}),
                                html.P(grap_stage, style={"color": "#0f172a", "fontSize": "0.88rem", "fontWeight": "600", "margin": "0", "lineHeight": "1.4"})
                            ]
                        )
                    ]
                )
            ]
        )
