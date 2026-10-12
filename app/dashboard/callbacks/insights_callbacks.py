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


def get_insights_dataframe() -> pd.DataFrame:
    """Load the official pivoted CPCB dataset."""
    candidates = [
        os.path.join(PROJECT_ROOT, "data", "cpcb_india_air_quality_pivoted.csv"),
        os.path.join(PROJECT_ROOT, "data", "sample_air_quality_dataset.csv"),
        "data/cpcb_india_air_quality_pivoted.csv"
    ]
    for p in candidates:
        if os.path.exists(p):
            return pd.read_csv(p)
    # Fallback to minimal dataframe
    return pd.DataFrame([
        {'city': 'Delhi', 'state': 'Delhi', 'latitude': 28.61, 'longitude': 77.20, 'aqi': 488.7, 'pm25': 285.0, 'pm10': 390.0, 'no2': 85.0, 'so2': 18.0, 'co': 45.0, 'station': 'Delhi Anand Vihar'},
        {'city': 'Bengaluru', 'state': 'Karnataka', 'latitude': 12.97, 'longitude': 77.59, 'aqi': 195.0, 'pm25': 45.0, 'pm10': 78.0, 'no2': 22.0, 'so2': 9.0, 'co': 12.0, 'station': 'Bengaluru BTM'}
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
            "✅ STATISTICALLY SIGNIFICANT (p < 0.05): Null Hypothesis (H0) Rejected! Major metropolitan centers suffer a statistically significant elevation in ambient toxic particulate compared to regional towns."
            if test_stats['is_significant'] else
            "❌ Failed to reject H0: No statistically significant difference detected."
        )

        ttest_cards = [
            create_metric_card(
                title="Metropolitan AQI Mean (N=94)",
                value=f"{test_stats['metro_mean']}",
                subtitle=f"Std Dev: {test_stats['metro_std']}"
            ),
            create_metric_card(
                title="Regional Towns AQI Mean (N=325)",
                value=f"{test_stats['regional_mean']}",
                subtitle=f"Std Dev: {test_stats['regional_std']}"
            ),
            create_metric_card(
                title="Calculated T-Statistic",
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
