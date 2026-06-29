import json
import logging
import os
from pathlib import Path

import dash
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
LOCATION_PATH = PROJECT_ROOT / "location.json"
DB_PATH = PROJECT_ROOT / "air_quality.db"

REFRESH_INTERVAL_MS = 5 * 60 * 1000
QUALITY_STALE_HOURS = 24
RAW_TABLE_CANDIDATES = ("air_quality", "air_quality_data")
PARAMETER_LABELS = {
    "pm25": "PM2.5",
    "pm10": "PM10",
    "no2": "NO2",
    "so2": "SO2",
    "o3": "O3",
}
WEEKDAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


with open(LOCATION_PATH, encoding="utf-8") as f:
    locations = json.load(f)


def parameter_label(parameter: str) -> str:
    return PARAMETER_LABELS.get(parameter, parameter.upper())


def empty_figure(message: str, loading: bool = False) -> go.Figure:
    fig = go.Figure()
    if loading:
        message = "Loading data..."
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
                "font": {"size": 15, "color": "#64748b"},
            }
        ],
        xaxis={"visible": False},
        yaxis={"visible": False},
        margin={"l": 24, "r": 24, "t": 36, "b": 24},
        height=420,
    )
    return fig


def style_figure(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin={"l": 48, "r": 24, "t": 56, "b": 44},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font={"family": "Segoe UI, Arial, sans-serif", "color": "#172033"},
        title={"font": {"size": 18}, "x": 0.02, "xanchor": "left"},
        hoverlabel={"bgcolor": "#172033", "font": {"color": "#ffffff"}},
    )
    fig.update_xaxes(gridcolor="#e2e8f0", zeroline=False)
    fig.update_yaxes(gridcolor="#e2e8f0", zeroline=False)
    return fig


def connect_read_only():
    return duckdb.connect(str(DB_PATH), read_only=True)


def get_raw_table_name(db_connection) -> str:
    table_names = {
        row[0]
        for row in db_connection.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'raw'
            """
        ).fetchall()
    }

    for table_name in RAW_TABLE_CANDIDATES:
        if table_name in table_names:
            return f"raw.{table_name}"

    raise RuntimeError(
        "No raw air-quality table found. Expected raw.air_quality or raw.air_quality_data."
    )


def load_air_quality_data(include_invalid: bool = False) -> pd.DataFrame:
    with connect_read_only() as db_connection:
        raw_table_name = get_raw_table_name(db_connection)
        value_filter = "" if include_invalid else """
            WHERE "value" IS NOT NULL
              AND "value" >= 0
        """
        query = f"""
            SELECT
                location_id,
                "location" AS location,
                "datetime" AS datetime,
                lat,
                lon,
                "parameter" AS parameter,
                units,
                "value" AS value,
                ingestion_datetime
            FROM {raw_table_name}
            {value_filter}
        """
        data = db_connection.execute(query).fetchdf()

    if data.empty:
        return data

    data["datetime"] = pd.to_datetime(data["datetime"])
    data["ingestion_datetime"] = pd.to_datetime(data["ingestion_datetime"])
    data["parameter"] = data["parameter"].astype(str).str.lower()
    return data


def get_latest_values_per_location() -> pd.DataFrame:
    raw_df = load_air_quality_data()

    if raw_df.empty:
        return raw_df

    latest_df = raw_df[
        raw_df["parameter"].isin(["pm10", "pm25", "so2"])
    ].sort_values("datetime")

    if latest_df.empty:
        return latest_df

    latest_df = latest_df.groupby(
        ["location_id", "location", "parameter"],
        as_index=False,
    ).tail(1)

    location_df = latest_df.groupby(
        ["location_id", "location"],
        as_index=False,
    ).agg(
        lat=("lat", "last"),
        lon=("lon", "last"),
        datetime=("datetime", "max"),
    )

    parameter_df = latest_df.pivot_table(
        index=["location_id", "location"],
        columns="parameter",
        values="value",
        aggfunc="last",
    ).reset_index()

    latest_values_df = location_df.merge(
        parameter_df,
        on=["location_id", "location"],
        how="left",
    )

    for parameter in ["pm10", "pm25", "so2"]:
        if parameter not in latest_values_df:
            latest_values_df[parameter] = None
        latest_values_df[parameter] = pd.to_numeric(
            latest_values_df[parameter],
            errors="coerce",
        ).fillna(0)

    return latest_values_df


def get_daily_air_quality_stats() -> pd.DataFrame:
    raw_df = load_air_quality_data()

    if raw_df.empty:
        return raw_df

    raw_df["measurement_date"] = raw_df["datetime"].dt.normalize()
    raw_df["weekday_number"] = raw_df["measurement_date"].dt.dayofweek
    raw_df["weekday"] = raw_df["measurement_date"].dt.day_name()
    raw_df["is_weekend"] = raw_df["weekday_number"].isin([5, 6]).astype(int)

    return raw_df.groupby(
        [
            "location_id",
            "location",
            "measurement_date",
            "weekday_number",
            "weekday",
            "is_weekend",
            "parameter",
            "units",
        ],
        as_index=False,
    ).agg(
        lat=("lat", "max"),
        lon=("lon", "max"),
        average_value=("value", "mean"),
    )


def get_raw_table_label() -> str:
    with connect_read_only() as db_connection:
        return get_raw_table_name(db_connection)


def get_data_quality_summary() -> dict:
    raw_df = load_air_quality_data(include_invalid=True)

    if raw_df.empty:
        return {
            "raw_df": raw_df,
            "clean_df": raw_df,
            "total_records": 0,
            "missing_values": 0,
            "negative_values": 0,
            "duplicate_records": 0,
            "stale_locations": 0,
            "latest_reading": None,
            "parameter_counts": pd.Series(dtype="int64"),
            "location_counts": pd.Series(dtype="int64"),
        }

    raw_df["value"] = pd.to_numeric(raw_df["value"], errors="coerce")
    clean_df = raw_df[raw_df["value"].notna() & (raw_df["value"] >= 0)].copy()
    duplicate_columns = ["location_id", "datetime", "parameter", "sensors_id"]
    duplicate_records = raw_df.duplicated(subset=duplicate_columns).sum()
    latest_reading = raw_df["datetime"].max()
    latest_by_location = raw_df.groupby("location")["datetime"].max()
    stale_cutoff = latest_reading - pd.Timedelta(hours=QUALITY_STALE_HOURS)

    return {
        "raw_df": raw_df,
        "clean_df": clean_df,
        "total_records": len(raw_df),
        "missing_values": int(raw_df["value"].isna().sum()),
        "negative_values": int((raw_df["value"] < 0).sum()),
        "duplicate_records": int(duplicate_records),
        "stale_locations": int((latest_by_location < stale_cutoff).sum()),
        "latest_reading": latest_reading,
        "parameter_counts": clean_df["parameter"].value_counts().sort_index(),
        "location_counts": clean_df["location"].value_counts().head(12),
    }


def make_location_options(raw_df: pd.DataFrame) -> list[dict]:
    if raw_df.empty:
        return [
            {"label": value, "value": value}
            for value in sorted(v for v in locations.values() if v)
        ]

    return [
        {"label": location, "value": location}
        for location in sorted(raw_df["location"].dropna().unique())
    ]


def make_parameter_options(raw_df: pd.DataFrame) -> list[dict]:
    if raw_df.empty:
        return []

    return [
        {"label": parameter_label(parameter), "value": parameter}
        for parameter in sorted(raw_df["parameter"].dropna().unique())
    ]


def metric_card(label: str, value: str, accent: str = "blue") -> html.Div:
    return html.Div(
        className=f"metric-card metric-card--{accent}",
        children=[
            html.Div(label, className="metric-label"),
            html.Div(value, className="metric-value"),
        ],
    )


def flow_node(title: str, value: str, accent: str) -> html.Div:
    return html.Div(
        className=f"flow-node flow-node--{accent}",
        children=[
            html.Div(title, className="flow-title"),
            html.Div(value, className="flow-value"),
        ],
    )


app = dash.Dash(
    __name__,
    title="Air Quality Dashboard",
    external_stylesheets=[
        "/assets/style-modern.css"
    ]
)
server = app.server


@server.route("/healthz")
def health_check():
    return "ok", 200

app.layout = html.Div(
    className="app-shell",
    children=[
        dcc.Interval(
            id="refresh-interval",
            interval=REFRESH_INTERVAL_MS,
            n_intervals=0,
        ),
        dcc.Download(id="download-data"),
        html.Header(
            className="topbar",
            children=[
                html.Div(
                    children=[
                        html.P("Air Quality Pipeline", className="eyebrow"),
                        html.H1("Monitoring Dashboard"),
                    ]
                ),
                html.Div(
                    className="status-strip",
                    children=[
                        html.Span("DuckDB", className="status-pill"),
                        html.Span("Auto refresh 5 min", className="status-text"),
                    ],
                ),
            ],
        ),
        html.Section(id="summary-cards", className="metric-grid"),
        dcc.Tabs(
            className="tabs",
            parent_className="tabs-wrap",
            children=[
                dcc.Tab(
                    label="Map",
                    className="tab",
                    selected_className="tab tab--selected",
                    children=[
                        html.Section(
                            className="panel",
                            children=[
                                dcc.Graph(
                                    id="map-view",
                                    config={"displaylogo": False},
                                    className="graph",
                                )
                            ],
                        )
                    ],
                ),
                dcc.Tab(
                    label="Trends",
                    className="tab",
                    selected_className="tab tab--selected",
                    children=[
                        html.Section(
                            className="control-panel",
                            children=[
                                html.Div(
                                    className="control",
                                    children=[
                                        html.Label("Location"),
                                        dcc.Dropdown(
                                            id="location-dropdown",
                                            clearable=False,
                                            multi=False,
                                            searchable=True,
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="control",
                                    children=[
                                        html.Label("Parameter"),
                                        dcc.Dropdown(
                                            id="parameter-dropdown",
                                            clearable=False,
                                            multi=False,
                                            searchable=True,
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="control control--date",
                                    children=[
                                        html.Label("Date Range"),
                                        dcc.DatePickerRange(
                                            id="date-picker-range",
                                            display_format="YYYY-MM-DD",
                                            className="date-picker",
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="control control--export",
                                    children=[
                                        html.Label("Export"),
                                        html.Button(
                                            "Download CSV",
                                            id="download-csv",
                                            n_clicks=0,
                                            className="export-button",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Section(
                            className="graph-grid",
                            children=[
                                html.Div(
                                    className="panel",
                                    children=[
                                        dcc.Graph(
                                            id="line-plot",
                                            config={"displaylogo": False},
                                            className="graph",
                                        )
                                    ],
                                ),
                                html.Div(
                                    className="panel",
                                    children=[
                                        dcc.Graph(
                                            id="box-plot",
                                            config={"displaylogo": False},
                                            className="graph",
                                        )
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
                dcc.Tab(
                    label="Quality",
                    className="tab",
                    selected_className="tab tab--selected",
                    children=[
                        html.Section(id="quality-cards", className="metric-grid"),
                        html.Section(
                            className="graph-grid",
                            children=[
                                html.Div(
                                    className="panel",
                                    children=[
                                        dcc.Graph(
                                            id="quality-parameter-chart",
                                            config={"displaylogo": False},
                                            className="graph",
                                        )
                                    ],
                                ),
                                html.Div(
                                    className="panel",
                                    children=[
                                        dcc.Graph(
                                            id="quality-location-chart",
                                            config={"displaylogo": False},
                                            className="graph",
                                        )
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
                dcc.Tab(
                    label="Data Flow",
                    className="tab",
                    selected_className="tab tab--selected",
                    children=[
                        html.Section(id="pipeline-flow", className="flow-grid"),
                        html.Section(
                            className="panel",
                            children=[
                                html.Div("Collection Snapshot", className="panel-title"),
                                html.Div(id="collection-details", className="detail-grid"),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)


@app.callback(
    [
        Output("summary-cards", "children"),
        Output("pipeline-flow", "children"),
        Output("collection-details", "children"),
    ],
    Input("refresh-interval", "n_intervals"),
)
def update_summary(_):
    try:
        raw_df = load_air_quality_data()
        raw_table_name = get_raw_table_label()
    except Exception as exc:
        logging.exception("Could not load dashboard summary")
        error_text = str(exc)
        return (
            [
                metric_card("Data Status", "Error", "red"),
                metric_card("Message", error_text[:46], "amber"),
            ],
            [flow_node("Database", "Not available", "red")],
            [html.Div(error_text, className="detail-item detail-item--wide")],
        )

    if raw_df.empty:
        return (
            [
                metric_card("Records", "0", "amber"),
                metric_card("Locations", "0", "blue"),
                metric_card("Parameters", "0", "green"),
                metric_card("Latest Reading", "No data", "red"),
            ],
            [
                flow_node("Source", "OpenAQ archive", "blue"),
                flow_node("Raw", raw_table_name, "green"),
                flow_node("Dashboard", "Waiting for records", "amber"),
            ],
            [html.Div("No records loaded yet.", className="detail-item detail-item--wide")],
        )

    latest_reading = raw_df["datetime"].max().strftime("%Y-%m-%d %H:%M")
    latest_ingestion = raw_df["ingestion_datetime"].max().strftime("%Y-%m-%d %H:%M")
    date_span = (
        f"{raw_df['datetime'].min().date().isoformat()} to "
        f"{raw_df['datetime'].max().date().isoformat()}"
    )

    summary_cards = [
        metric_card("Records", f"{len(raw_df):,}", "blue"),
        metric_card("Locations", f"{raw_df['location'].nunique():,}", "green"),
        metric_card("Parameters", f"{raw_df['parameter'].nunique():,}", "amber"),
        metric_card("Latest Reading", latest_reading, "red"),
    ]

    pipeline_flow = [
        flow_node("Source", "OpenAQ S3 archive", "blue"),
        flow_node("Extract", "DuckDB read_csv", "green"),
        flow_node("Raw", raw_table_name, "amber"),
        flow_node("Dashboard", "Dash + Plotly", "red"),
    ]

    collection_details = [
        html.Div(
            children=[html.Span("Date span"), html.Strong(date_span)],
            className="detail-item",
        ),
        html.Div(
            children=[html.Span("Last ingestion"), html.Strong(latest_ingestion)],
            className="detail-item",
        ),
        html.Div(
            children=[
                html.Span("Parameters"),
                html.Strong(", ".join(parameter_label(p) for p in sorted(raw_df["parameter"].unique()))),
            ],
            className="detail-item detail-item--wide",
        ),
    ]

    return summary_cards, pipeline_flow, collection_details


@app.callback(
    [
        Output("quality-cards", "children"),
        Output("quality-parameter-chart", "figure"),
        Output("quality-location-chart", "figure"),
    ],
    Input("refresh-interval", "n_intervals"),
)
def update_quality(_):
    try:
        quality = get_data_quality_summary()
    except Exception:
        logging.exception("Could not load data quality summary")
        return (
            [
                metric_card("Quality Status", "Error", "red"),
                metric_card("Records", "Unavailable", "amber"),
            ],
            empty_figure("Data quality could not be loaded."),
            empty_figure("Data quality could not be loaded."),
        )

    if quality["total_records"] == 0:
        return (
            [
                metric_card("Records", "0", "amber"),
                metric_card("Missing Values", "0", "blue"),
                metric_card("Negative Values", "0", "green"),
                metric_card("Duplicates", "0", "red"),
            ],
            empty_figure("No records to profile yet."),
            empty_figure("No records to profile yet."),
        )

    stale_label = f">{QUALITY_STALE_HOURS}h"
    quality_cards = [
        metric_card("Records Checked", f"{quality['total_records']:,}", "blue"),
        metric_card("Missing Values", f"{quality['missing_values']:,}", "amber"),
        metric_card("Negative Values", f"{quality['negative_values']:,}", "red"),
        metric_card("Stale Locations", f"{quality['stale_locations']:,} {stale_label}", "green"),
    ]

    parameter_counts = quality["parameter_counts"].rename_axis("parameter").reset_index(name="records")
    parameter_counts["parameter_label"] = parameter_counts["parameter"].map(parameter_label)
    parameter_fig = px.bar(
        parameter_counts,
        x="parameter_label",
        y="records",
        color="parameter_label",
        title="Valid Records by Parameter",
        labels={"parameter_label": "Parameter", "records": "Records"},
        color_discrete_sequence=["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"],
    )
    parameter_fig.update_layout(showlegend=False)
    style_figure(parameter_fig)

    location_counts = quality["location_counts"].rename_axis("location").reset_index(name="records")
    location_fig = px.bar(
        location_counts,
        x="records",
        y="location",
        orientation="h",
        title="Top Locations by Record Count",
        labels={"records": "Records", "location": "Location"},
        color_discrete_sequence=["#10b981"],
    )
    location_fig.update_layout(yaxis={"categoryorder": "total ascending"})
    style_figure(location_fig)

    return quality_cards, parameter_fig, location_fig


@app.callback(
    [
        Output("location-dropdown", "options"),
        Output("parameter-dropdown", "options"),
        Output("location-dropdown", "value"),
        Output("parameter-dropdown", "value"),
        Output("date-picker-range", "start_date"),
        Output("date-picker-range", "end_date"),
        Output("date-picker-range", "min_date_allowed"),
        Output("date-picker-range", "max_date_allowed"),
    ],
    Input("refresh-interval", "n_intervals"),
    [
        State("location-dropdown", "value"),
        State("parameter-dropdown", "value"),
        State("date-picker-range", "start_date"),
        State("date-picker-range", "end_date"),
    ],
)
def update_controls(_, current_location, current_parameter, current_start, current_end):
    try:
        raw_df = load_air_quality_data()
    except Exception:
        logging.exception("Could not load dashboard controls")
        return [], [], None, None, None, None, None, None

    location_options = make_location_options(raw_df)
    parameter_options = make_parameter_options(raw_df)

    if raw_df.empty or not location_options or not parameter_options:
        return location_options, parameter_options, None, None, None, None, None, None

    location_values = {option["value"] for option in location_options}
    parameter_values = {option["value"] for option in parameter_options}

    selected_location = (
        current_location if current_location in location_values else location_options[0]["value"]
    )
    location_parameter_values = set(
        raw_df.loc[raw_df["location"] == selected_location, "parameter"].dropna().unique()
    )
    if not location_parameter_values:
        location_parameter_values = parameter_values
    selected_parameter = (
        current_parameter
        if current_parameter in parameter_values and current_parameter in location_parameter_values
        else sorted(location_parameter_values)[0]
    )

    min_date = raw_df["datetime"].min().date().isoformat()
    max_date = raw_df["datetime"].max().date().isoformat()
    start_date = current_start or min_date
    end_date = current_end or max_date

    return (
        location_options,
        parameter_options,
        selected_location,
        selected_parameter,
        start_date,
        end_date,
        min_date,
        max_date,
    )


@app.callback(
    Output("map-view", "figure"),
    Input("refresh-interval", "n_intervals"),
)
def update_map(_):
    try:
        latest_values_df = get_latest_values_per_location()
    except Exception:
        logging.exception("Could not update map")
        return empty_figure("Map data could not be loaded.")

    if latest_values_df.empty:
        return empty_figure("No map data available.")

    latest_values_df = latest_values_df.dropna(subset=["lat", "lon"])
    if latest_values_df.empty:
        return empty_figure("No coordinates available.")

    center = {
        "lat": latest_values_df["lat"].mean(),
        "lon": latest_values_df["lon"].mean(),
    }

    fig = px.scatter_map(
        latest_values_df,
        lat="lat",
        lon="lon",
        color="pm25",
        size=latest_values_df["pm25"].clip(lower=1),
        hover_name="location",
        hover_data={
            "lat": False,
            "lon": False,
            "datetime": True,
            "pm10": ":.2f",
            "pm25": ":.2f",
            "so2": ":.2f",
        },
        color_continuous_scale=["#10b981", "#f59e0b", "#ef4444"],
        range_color=[0, 100],
        center=center,
        zoom=5.2,
        title="Latest Sensor Readings (PM2.5)",
    )

    fig.update_layout(
        map_style="open-street-map",
        coloraxis_colorbar={"title": "PM2.5"},
        margin={"l": 0, "r": 0, "t": 56, "b": 0},
        height=680,
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Segoe UI, Arial, sans-serif", "color": "#172033"},
        title={"font": {"size": 18}, "x": 0.02, "xanchor": "left"},
    )
    return fig


@app.callback(
    [
        Output("line-plot", "figure"),
        Output("box-plot", "figure"),
    ],
    [
        Input("location-dropdown", "value"),
        Input("parameter-dropdown", "value"),
        Input("date-picker-range", "start_date"),
        Input("date-picker-range", "end_date"),
        Input("refresh-interval", "n_intervals"),
    ],
)
def update_plots(
    selected_location,
    selected_parameter,
    start_date,
    end_date,
    _,
):
    if not all([selected_location, selected_parameter, start_date, end_date]):
        return empty_figure("Choose a location and parameter."), empty_figure(
            "Choose a location and parameter."
        )

    try:
        daily_stats_df = get_daily_air_quality_stats()
    except Exception:
        logging.exception("Could not update plots")
        return empty_figure("Trend data could not be loaded."), empty_figure(
            "Distribution data could not be loaded."
        )

    filtered_df = daily_stats_df[
        (daily_stats_df["location"] == selected_location)
        & (daily_stats_df["parameter"] == selected_parameter)
    ].copy()

    if filtered_df.empty:
        label = parameter_label(selected_parameter)
        return empty_figure(f"No {label} trend data for this location."), empty_figure(
            f"No {label} distribution data for this location."
        )

    measurement_dates = pd.to_datetime(filtered_df["measurement_date"])
    filtered_df = filtered_df[
        (measurement_dates >= pd.to_datetime(start_date))
        & (measurement_dates <= pd.to_datetime(end_date))
    ]

    if filtered_df.empty:
        return empty_figure("No data in this date range."), empty_figure(
            "No data in this date range."
        )

    unit = filtered_df["units"].dropna().iloc[0]
    label = parameter_label(selected_parameter)
    labels = {
        "average_value": unit,
        "measurement_date": "Date",
        "weekday": "Weekday",
    }

    line_fig = px.line(
        filtered_df.sort_values(by="measurement_date"),
        x="measurement_date",
        y="average_value",
        markers=True,
        labels=labels,
        title=f"{label} Daily Average",
    )
    line_fig.update_traces(
        line={"color": "#3b82f6", "width": 3},
        marker={"size": 7, "color": "#3b82f6"}
    )
    style_figure(line_fig)

    box_fig = px.box(
        filtered_df.sort_values(by="weekday_number"),
        x="weekday",
        y="average_value",
        points="all",
        labels=labels,
        category_orders={"weekday": WEEKDAY_ORDER},
        title=f"{label} Distribution by Weekday",
    )
    box_fig.update_traces(
        marker={"color": "#10b981", "size": 7},
        line={"color": "#059669"}
    )
    style_figure(box_fig)

    return line_fig, box_fig


@app.callback(
    Output("download-data", "data"),
    Input("download-csv", "n_clicks"),
    [
        State("location-dropdown", "value"),
        State("parameter-dropdown", "value"),
        State("date-picker-range", "start_date"),
        State("date-picker-range", "end_date"),
    ],
    prevent_initial_call=True,
)
def download_filtered_data(n_clicks, selected_location, selected_parameter, start_date, end_date):
    if not n_clicks or not all([selected_location, selected_parameter, start_date, end_date]):
        return None

    daily_stats_df = get_daily_air_quality_stats()
    measurement_dates = pd.to_datetime(daily_stats_df["measurement_date"])
    filtered_df = daily_stats_df[
        (daily_stats_df["location"] == selected_location)
        & (daily_stats_df["parameter"] == selected_parameter)
        & (measurement_dates >= pd.to_datetime(start_date))
        & (measurement_dates <= pd.to_datetime(end_date))
    ].copy()

    filename_parameter = selected_parameter.replace(" ", "_")
    filename_location = selected_location.lower().replace(" ", "_").replace("/", "_")
    return dcc.send_data_frame(
        filtered_df.to_csv,
        f"air_quality_{filename_location}_{filename_parameter}.csv",
        index=False,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8050"))
    debug = os.environ.get("DASH_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
