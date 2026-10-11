"""
Machine Learning Visualization Charts
Interactive Plotly charts for model evaluation, feature impact, and predictions.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from app.dashboard.components.charts import style_figure, create_empty_figure


def create_actual_vs_predicted_chart(data: List[Dict[str, float]], title: str = "Actual vs. Predicted AQI") -> go.Figure:
    """Scatter plot of actual values vs model predictions with ideal 45-degree reference line."""
    if not data:
        return create_empty_figure("No prediction data available")
        
    df = pd.DataFrame(data)
    if "Actual" not in df.columns or "Predicted" not in df.columns:
        return create_empty_figure("Invalid prediction data schema")
        
    min_val = min(df["Actual"].min(), df["Predicted"].min()) * 0.95
    max_val = max(df["Actual"].max(), df["Predicted"].max()) * 1.05
    
    fig = go.Figure()
    
    # Scatter points
    fig.add_trace(go.Scatter(
        x=df["Actual"],
        y=df["Predicted"],
        mode="markers",
        name="Test Predictions",
        marker=dict(
            color=df.get("Residual", df["Actual"] - df["Predicted"]),
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title="Residual (Act - Pred)", thickness=15),
            size=7,
            opacity=0.75
        ),
        hovertemplate="<b>Actual:</b> %{x:.1f}<br><b>Predicted:</b> %{y:.1f}<extra></extra>"
    ))
    
    # Ideal 1:1 line
    fig.add_trace(go.Scatter(
        x=[min_val, max_val],
        y=[min_val, max_val],
        mode="lines",
        name="Perfect Fit (y = x)",
        line=dict(color="#ef4444", dash="dash", width=2.5)
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Actual Values (Ground Truth)",
        yaxis_title="Model Predicted Values",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    
    return style_figure(fig)


def create_feature_importance_chart(importance_data: List[Dict[str, Any]], title: str = "Feature Importance Ranking") -> go.Figure:
    """Horizontal bar chart showing relative influence of pollutants on AQI."""
    if not importance_data:
        return create_empty_figure("No feature importance data available")
        
    df = pd.DataFrame(importance_data)
    # Sort ascending so largest is on top in horizontal bar
    df = df.sort_values(by="importance", ascending=True)
    
    fig = go.Figure(go.Bar(
        x=df["importance"],
        y=df["feature"],
        orientation="h",
        marker=dict(
            color=df["importance"],
            colorscale="Tealgrn",
            showscale=False
        ),
        text=df["importance"].apply(lambda v: f"{v:.3f}"),
        textposition="auto"
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Relative Importance Weight",
        yaxis_title="Feature / Pollutant",
        margin=dict(l=120, r=30, t=56, b=44)
    )
    
    return style_figure(fig)


def create_residuals_chart(residuals: List[float], title: str = "Prediction Residuals Distribution") -> go.Figure:
    """Histogram of prediction residuals with mean zero reference."""
    if not residuals:
        return create_empty_figure("No residual data available")
        
    res_arr = np.array(residuals)
    mean_res = np.mean(res_arr)
    std_res = np.std(res_arr)
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=res_arr,
        nbinsx=35,
        marker_color="#3b82f6",
        opacity=0.75,
        name="Residuals",
        hovertemplate="Error Bin: %{x:.2f}<br>Count: %{y}<extra></extra>"
    ))
    
    # Zero line
    fig.add_vline(
        x=0, 
        line_width=2.5, 
        line_dash="dash", 
        line_color="#ef4444",
        annotation_text="Zero Error Line", 
        annotation_position="top right"
    )
    
    fig.update_layout(
        title=f"{title} (Mean: {mean_res:.2f}, Std: {std_res:.2f})",
        xaxis_title="Prediction Error (Actual - Predicted)",
        yaxis_title="Frequency Count",
        bargap=0.08
    )
    
    return style_figure(fig)


def create_correlation_heatmap(corr_data: Dict[str, Any], title: str = "Pollutant Correlation Matrix") -> go.Figure:
    """Heatmap showing pairwise linear correlation between features."""
    if not corr_data or "z" not in corr_data:
        return create_empty_figure("No correlation data available")
        
    z = corr_data["z"]
    x = corr_data["x"]
    y = corr_data["y"]
    
    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=x,
        y=y,
        colorscale="RdBu_r",
        zmin=-1,
        zmax=1,
        text=z,
        texttemplate="%{text}",
        hoverongaps=False
    ))
    
    fig.update_layout(
        title=title,
        height=430,
        margin=dict(l=80, r=40, t=56, b=60)
    )
    
    return style_figure(fig)


def create_confusion_matrix_chart(cm_data: Dict[str, Any], title: str = "Classification Confusion Matrix") -> go.Figure:
    """Heatmap of confusion matrix for AQI Category classification."""
    if not cm_data or "z" not in cm_data:
        return create_empty_figure("No confusion matrix available")
        
    z = cm_data["z"]
    x = cm_data["x"]
    y = cm_data["y"]
    
    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=x,
        y=y,
        colorscale="Blues",
        text=z,
        texttemplate="%{text}",
        hoverongaps=False
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Predicted Class",
        yaxis_title="True Class",
        height=420
    )
    
    return style_figure(fig)


def create_aqi_gauge(aqi_value: float, category: str, color: str) -> go.Figure:
    """Interactive circular gauge showing predicted AQI with colored standard bands."""
    val = float(aqi_value) if aqi_value is not None else 0.0
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"<b>Predicted AQI: {category}</b>", 'font': {'size': 20, 'color': color}},
        gauge={
            'axis': {'range': [0, 500], 'tickwidth': 1, 'tickcolor': "#475569"},
            'bar': {'color': color, 'thickness': 0.3},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#cbd5e1",
            'steps': [
                {'range': [0, 50], 'color': '#d1fae5'},       # Good (green)
                {'range': [50, 100], 'color': '#dbeafe'},     # Satisfactory (blue)
                {'range': [100, 200], 'color': '#fef3c7'},    # Moderate (yellow)
                {'range': [200, 300], 'color': '#ffedd5'},    # Poor (orange)
                {'range': [300, 400], 'color': '#fee2e2'},    # Very Poor (red)
                {'range': [400, 500], 'color': '#f3e8ff'},    # Severe (purple/dark)
            ],
            'threshold': {
                'line': {'color': color, 'width': 5},
                'thickness': 0.8,
                'value': val
            }
        }
    ))
    
    fig.update_layout(
        height=320,
        margin=dict(l=30, r=30, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Segoe UI, Arial, sans-serif")
    )
    
    return fig
