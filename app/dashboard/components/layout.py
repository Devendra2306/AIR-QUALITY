from dash import html, dcc
from typing import List, Optional


def create_header(
    title: str = "Air Quality Monitoring",
    subtitle: str = "Real-time Environmental Data Dashboard"
) -> html.Div:
    """Create dashboard header."""
    return html.Header(
        className="dashboard-header",
        children=[
            html.Div(
                className="header-content",
                children=[
                    html.Div(
                        className="header-text",
                        children=[
                            html.Span(
                                subtitle,
                                className="header-subtitle"
                            ),
                            html.H1(title, className="header-title"),
                        ]
                    ),
                    html.Div(
                        className="header-status",
                        children=[
                            html.Span(
                                "● Live",
                                className="status-indicator status-live"
                            ),
                            html.Span(
                                "Auto-refresh: 5 min",
                                className="status-text"
                            ),
                        ]
                    )
                ]
            )
        ]
    )


def create_metric_card(
    label: str,
    value: str,
    accent: str = "blue",
    trend: Optional[str] = None,
    icon: Optional[str] = None
) -> html.Div:
    """Create a metric card."""
    return html.Div(
        className=f"metric-card metric-card--{accent}",
        children=[
            html.Div(
                className="metric-header",
                children=[
                    html.Span(label, className="metric-label"),
                    html.Span(icon or "", className="metric-icon")
                ]
            ),
            html.Div(value, className="metric-value"),
            html.Span(trend or "", className="metric-trend")
        ]
    )


def create_metric_grid(
    cards: List[html.Div],
    columns: int = 4
) -> html.Div:
    """Create a grid of metric cards."""
    return html.Div(
        className=f"metric-grid metric-grid--{columns}",
        children=cards
    )


def create_tab(
    label: str,
    value: str,
    children: List,
    selected: bool = False
) -> dcc.Tab:
    """Create a dashboard tab."""
    return dcc.Tab(
        label=label,
        value=value,
        children=children,
        selected_className="tab--selected",
        className="tab"
    )


def create_panel(
    title: Optional[str] = None,
    children: List = None,
    className: str = "panel"
) -> html.Div:
    """Create a content panel."""
    panel_children = []
    
    if title:
        panel_children.append(html.H3(title, className="panel-title"))
    
    if children:
        panel_children.extend(children)
    
    return html.Div(
        className=className,
        children=panel_children
    )


def create_loading_spinner() -> html.Div:
    """Create a loading spinner."""
    return html.Div(
        className="loading-container",
        children=[
            html.Div(className="loading-spinner"),
            html.P("Loading data...", className="loading-text")
        ]
    )


def create_empty_state(
    message: str,
    icon: str = "📊"
) -> html.Div:
    """Create an empty state component."""
    return html.Div(
        className="empty-state",
        children=[
            html.Div(icon, className="empty-state-icon"),
            html.P(message, className="empty-state-text")
        ]
    )
