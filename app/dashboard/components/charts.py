import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Any, Optional
import pandas as pd
from app.config.logging_config import logger


def create_empty_figure(
    message: str = "No data available",
    height: int = 420
) -> go.Figure:
    """Create an empty placeholder figure."""
    fig = go.Figure()
    fig.update_layout(
        template="plotly_white",
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 15, "color": "#64748b"}
            }
        ],
        xaxis={"visible": False},
        yaxis={"visible": False},
        margin={"l": 24, "r": 24, "t": 36, "b": 24},
        height=height
    )
    return fig


def style_figure(
    fig: go.Figure,
    height: int = 420,
    title: Optional[str] = None
) -> go.Figure:
    """Apply consistent styling to figures."""
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin={"l": 48, "r": 24, "t": 56, "b": 44},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font={"family": "Segoe UI, Arial, sans-serif", "color": "#0f172a"},
        title={"font": {"size": 18}, "x": 0.02, "xanchor": "left"},
        hoverlabel={"bgcolor": "#0f172a", "font": {"color": "#ffffff"}},
    )
    
    if title:
        fig.update_layout(title=title)
    
    fig.update_xaxes(gridcolor="#e2e8f0", zeroline=False)
    fig.update_yaxes(gridcolor="#e2e8f0", zeroline=False)
    
    return fig


def create_map_figure(
    data: pd.DataFrame,
    color_column: str = "value",
    size_column: Optional[str] = None,
    hover_name: str = "location",
    hover_data: Optional[List[str]] = None,
    title: str = "Sensor Map"
) -> go.Figure:
    """Create an interactive map figure."""
    if data.empty:
        return create_empty_figure("No map data available")
    
    data = data.dropna(subset=["latitude", "longitude"])
    if data.empty:
        return create_empty_figure("No coordinates available")
    
    center = {
        "lat": data["latitude"].mean(),
        "lon": data["longitude"].mean()
    }
    
    size = data[size_column].clip(lower=1) if size_column else None
    
    fig = px.scatter_map(
        data,
        lat="latitude",
        lon="longitude",
        color=color_column,
        size=size,
        hover_name=hover_name,
        hover_data=hover_data or [],
        color_continuous_scale=["#10b981", "#f59e0b", "#ef4444"],
        range_color=[0, 100],
        center=center,
        zoom=5,
        title=title
    )
    
    fig.update_layout(
        map_style="open-street-map",
        coloraxis_colorbar={"title": color_column},
        margin={"l": 0, "r": 0, "t": 56, "b": 0},
        height=680,
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Segoe UI, Arial, sans-serif", "color": "#0f172a"},
        title={"font": {"size": 18}, "x": 0.02, "xanchor": "left"}
    )
    
    return fig


def create_line_chart(
    data: pd.DataFrame,
    x_column: str,
    y_column: str,
    title: str,
    color: str = "#3b82f6"
) -> go.Figure:
    """Create a line chart."""
    if data.empty:
        return create_empty_figure("No data available")
    
    fig = px.line(
        data.sort_values(by=x_column),
        x=x_column,
        y=y_column,
        markers=True,
        title=title
    )
    
    fig.update_traces(
        line={"color": color, "width": 3},
        marker={"size": 7, "color": color}
    )
    
    return style_figure(fig)


def create_box_plot(
    data: pd.DataFrame,
    x_column: str,
    y_column: str,
    title: str,
    color: str = "#10b981"
) -> go.Figure:
    """Create a box plot."""
    if data.empty:
        return create_empty_figure("No data available")
    
    fig = px.box(
        data,
        x=x_column,
        y=y_column,
        points="all",
        title=title
    )
    
    fig.update_traces(
        marker={"color": color, "size": 7},
        line={"color": color}
    )
    
    return style_figure(fig)


def create_bar_chart(
    data: pd.DataFrame,
    x_column: str,
    y_column: str,
    title: str,
    color: str = "#3b82f6",
    orientation: str = "v"
) -> go.Figure:
    """Create a bar chart."""
    if data.empty:
        return create_empty_figure("No data available")
    
    fig = px.bar(
        data,
        x=x_column if orientation == "v" else y_column,
        y=y_column if orientation == "v" else x_column,
        orientation=orientation,
        title=title
    )
    
    fig.update_traces(marker_color=color)
    
    return style_figure(fig)


def create_gauge_chart(
    value: float,
    title: str,
    min_value: float = 0,
    max_value: float = 100,
    thresholds: Optional[Dict[str, float]] = None
) -> go.Figure:
    """Create a gauge chart for AQI-style indicators."""
    if thresholds is None:
        thresholds = {"good": 50, "moderate": 100, "unhealthy": 150}
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        gauge={
            'axis': {'range': [min_value, max_value]},
            'bar': {'color': "#3b82f6"},
            'steps': [
                {'range': [min_value, thresholds.get("good", 50)], 'color': "#10b981"},
                {'range': [thresholds.get("good", 50), thresholds.get("moderate", 100)], 'color': "#f59e0b"},
                {'range': [thresholds.get("moderate", 100), max_value], 'color': "#ef4444"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': thresholds.get("moderate", 100)
            }
        }
    ))
    
    fig.update_layout(height=300, margin={"l": 20, "r": 20, "t": 40, "b": 20})
    
    return fig


def create_heatmap(
    data: pd.DataFrame,
    x_column: str,
    y_column: str,
    z_column: str,
    title: str
) -> go.Figure:
    """Create a heatmap."""
    if data.empty:
        return create_empty_figure("No data available")
    
    pivot_data = data.pivot_table(
        values=z_column,
        index=y_column,
        columns=x_column,
        aggfunc='mean'
    )
    
    fig = px.imshow(
        pivot_data,
        title=title,
        color_continuous_scale="Viridis"
    )
    
    return style_figure(fig)
