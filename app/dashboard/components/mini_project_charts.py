"""
Mini Project Analytical & Machine Learning Visualizations
Directly mirrors the exploratory data analysis and ML models from:
'mini project final set/Air_Quality_Mini_Project_India_Dataset (1).ipynb'
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from app.dashboard.components.charts import style_figure
from dash import html



# Standard CPCB AQI Category Colors
AQI_COLORS = {
    "Good": "#10b981",          # Green (0-50)
    "Satisfactory": "#84cc16",  # Light Green (51-100)
    "Moderate": "#eab308",      # Yellow (101-200)
    "Poor": "#f97316",          # Orange (201-300)
    "Very Poor": "#ef4444",     # Red (301-400)
    "Severe": "#7f1d1d"         # Maroon (401-500)
}


def create_aqi_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """Visualize AQI distribution histogram matching Notebook Step 4."""
    fig = px.histogram(
        df,
        x="aqi",
        nbins=35,
        marginal="box",
        color="aqi_category",
        color_discrete_map=AQI_COLORS,
        title="Air Quality Index (AQI) Distribution & Category Spread",
        labels={"aqi": "Air Quality Index (AQI)", "count": "Frequency", "aqi_category": "Category"}
    )
    
    # Add vertical reference lines for thresholds
    fig.add_vline(x=50, line_dash="dash", line_color="#10b981", annotation_text="Good (50)")
    fig.add_vline(x=100, line_dash="dash", line_color="#84cc16", annotation_text="Satisfactory (100)")
    fig.add_vline(x=200, line_dash="dash", line_color="#eab308", annotation_text="Moderate (200)")
    
    fig.update_layout(
        xaxis_title="Air Quality Index (AQI)",
        yaxis_title="Observation Count",
        legend_title="AQI Bucket"
    )
    return style_figure(fig)


def create_category_pie_chart(df: pd.DataFrame) -> go.Figure:
    """Donut chart showing proportion of AQI categories."""
    cat_counts = df["aqi_category"].value_counts().reset_index()
    cat_counts.columns = ["Category", "Count"]
    
    fig = px.pie(
        cat_counts,
        values="Count",
        names="Category",
        hole=0.45,
        color="Category",
        color_discrete_map=AQI_COLORS,
        title="Proportion of Observations by AQI Category"
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return style_figure(fig)


def create_pollutant_levels_chart(df: pd.DataFrame) -> go.Figure:
    """Mean concentration of criteria pollutants matching Notebook Step 5."""
    pollutants = ["pm25", "pm10", "no2", "so2", "co", "o3"]
    labels = ["PM2.5 (µg/m³)", "PM10 (µg/m³)", "NO2 (µg/m³)", "SO2 (µg/m³)", "CO (mg/m³)", "O3 (µg/m³)"]
    
    means = [round(float(df[col].mean()), 2) for col in pollutants if col in df.columns]
    names = [label for col, label in zip(pollutants, labels) if col in df.columns]
    
    bar_colors = ["#ef4444", "#f97316", "#3b82f6", "#8b5cf6", "#10b981", "#06b6d4"]
    
    fig = go.Figure(data=[
        go.Bar(
            x=names,
            y=means,
            text=means,
            textposition="auto",
            marker_color=bar_colors[:len(means)],
            opacity=0.9
        )
    ])
    fig.update_layout(
        title="Mean Concentrations of Monitored Criteria Pollutants",
        xaxis_title="Pollutant Parameter",
        yaxis_title="Average Concentration",
        margin=dict(l=20, r=20, t=50, b=30)
    )
    return style_figure(fig)


def create_city_pollutant_chart(df: pd.DataFrame) -> go.Figure:
    """Mean AQI and PM2.5 compared across major urban airsheds."""
    city_summary = df.groupby("city").agg({
        "aqi": "mean",
        "pm25": "mean",
        "pm10": "mean"
    }).round(1).reset_index()
    
    fig = go.Figure(data=[
        go.Bar(name="Mean AQI", x=city_summary["city"], y=city_summary["aqi"], marker_color="#2563eb"),
        go.Bar(name="PM2.5 (µg/m³)", x=city_summary["city"], y=city_summary["pm25"], marker_color="#ef4444"),
        go.Bar(name="PM10 (µg/m³)", x=city_summary["city"], y=city_summary["pm10"], marker_color="#f59e0b")
    ])
    fig.update_layout(
        barmode="group",
        title="Air Quality & Particulate Severity Across Monitored Urban Airsheds",
        xaxis_title="Urban Airshed / City",
        yaxis_title="Mean Concentration / Index",
        legend_title="Metric"
    )
    return style_figure(fig)


def create_temporal_trends_chart(df: pd.DataFrame, city: Optional[str] = None) -> go.Figure:
    """AQI over time longitudinal trajectory matching Notebook Step 6."""
    plot_df = df.copy()
    if city and city in plot_df["city"].values:
        plot_df = plot_df[plot_df["city"] == city]
        title = f"Temporal Trajectory of AQI Over Time: {city}"
    else:
        title = "National Multi-City Aggregate AQI Over Time"
        
    plot_df["timestamp"] = pd.to_datetime(plot_df["timestamp"])
    plot_df = plot_df.sort_values("timestamp")
    
    # Calculate rolling 7-day average if sufficient points
    plot_df["aqi_rolling"] = plot_df["aqi"].rolling(window=14, min_periods=1).mean()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=plot_df["timestamp"],
        y=plot_df["aqi"],
        mode="markers",
        marker=dict(size=4, color="#94a3b8", opacity=0.5),
        name="Recorded AQI Observation"
    ))
    fig.add_trace(go.Scatter(
        x=plot_df["timestamp"],
        y=plot_df["aqi_rolling"],
        mode="lines",
        line=dict(color="#2563eb", width=2.5),
        name="Trend (Moving Average)"
    ))
    fig.update_layout(
        title=title,
        xaxis_title="Observation Date / Time",
        yaxis_title="Air Quality Index (AQI)",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    return style_figure(fig)


def create_correlation_heatmap(df: pd.DataFrame) -> go.Figure:
    """Inter-pollutant correlation heatmap matching Notebook Step 7."""
    features = ["pm25", "pm10", "no2", "so2", "co", "o3", "temperature", "humidity", "wind_speed", "aqi"]
    corr_df = df[[c for c in features if c in df.columns]].corr().round(2)
    
    labels = [c.upper() for c in corr_df.columns]
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_df.values,
        x=labels,
        y=labels,
        colorscale="RdBu_r",
        zmin=-1,
        zmax=1,
        text=corr_df.values,
        texttemplate="%{text}",
        colorbar=dict(title="Correlation")
    ))
    fig.update_layout(
        title="Inter-Pollutant & Meteorological Correlation Matrix (vs AQI)",
        margin=dict(l=40, r=40, t=50, b=40)
    )
    return style_figure(fig)


def train_mini_project_models(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Train and compare the exact models from the Colab Notebook:
    - Linear Regression
    - PCA + Linear Regression
    - Random Forest Regressor
    """
    from sklearn.impute import SimpleImputer
    
    # Clean and find features
    df_clean = df.copy()
    col_map = {c: str(c).lower().replace(".", "").replace("-", "").strip() for c in df_clean.columns}
    df_clean = df_clean.rename(columns=col_map)
    
    if "aqi" not in df_clean.columns:
        raise ValueError("The dataset does not contain an 'aqi' target column.")
        
    df_clean = df_clean.dropna(subset=["aqi"]).copy()
    
    feature_cols = ["pm25", "pm10", "no2", "so2", "co", "o3", "temperature", "humidity", "wind_speed"]
    features = [c for c in feature_cols if c in df_clean.columns]
    
    # If standard pollutant columns are not present, select all valid numeric columns
    if len(features) < 2:
        exclude = {"aqi", "id", "year", "month", "day", "hour", "latitude", "longitude"}
        num_cols = df_clean.select_dtypes(include=[np.number]).columns.tolist()
        features = [c for c in num_cols if c not in exclude]
        
    if not features:
        raise ValueError("No valid numeric feature columns found to train models.")
        
    X = df_clean[features].copy()
    y = df_clean["aqi"].copy()
    
    # Cap samples to 8000 if massive to ensure instant training and low memory on Render
    if len(X) > 8000:
        idx = np.random.RandomState(42).choice(len(X), size=8000, replace=False)
        X = X.iloc[idx].copy()
        y = y.iloc[idx].copy()
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )
    
    # 1. Linear Regression Pipeline with Median Imputer (Notebook Step 8)
    linear_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", LinearRegression())
    ])
    linear_pipeline.fit(X_train, y_train)
    lr_pred = linear_pipeline.predict(X_test)
    
    # 2. PCA + Linear Regression Pipeline with Median Imputer (Notebook Step 8)
    n_comp = min(len(features), 6) if len(features) > 2 else len(features)
    pca_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("pca", PCA(n_components=min(0.95, n_comp), random_state=42)),
        ("model", LinearRegression())
    ])
    pca_pipeline.fit(X_train, y_train)
    pca_pred = pca_pipeline.predict(X_test)
    pca_step = pca_pipeline.named_steps["pca"]
    
    # 3. Random Forest Regressor Pipeline
    rf_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=1))
    ])
    rf_pipeline.fit(X_train, y_train)
    rf_pred = rf_pipeline.predict(X_test)
    
    # Model evaluation metrics (Notebook Step 9)
    def evaluate(actual, predicted):
        mse = mean_squared_error(actual, predicted)
        return {
            "mae": round(float(mean_absolute_error(actual, predicted)), 3),
            "mse": round(float(mse), 3),
            "rmse": round(float(np.sqrt(mse)), 3),
            "r2": round(float(r2_score(actual, predicted)), 4)
        }
        
    lr_metrics = evaluate(y_test, lr_pred)
    pca_metrics = evaluate(y_test, pca_pred)
    rf_metrics = evaluate(y_test, rf_pred)
    
    return {
        "X_train_count": len(X_train),
        "X_test_count": len(X_test),
        "features": features,
        "y_test": y_test.values,
        "lr_pred": lr_pred,
        "pca_pred": pca_pred,
        "rf_pred": rf_pred,
        "lr_metrics": lr_metrics,
        "pca_metrics": pca_metrics,
        "rf_metrics": rf_metrics,
        "pca_n_components": int(pca_step.n_components_),
        "pca_variance_ratio": [round(float(v) * 100, 2) for v in pca_step.explained_variance_ratio_],
        "linear_pipeline": linear_pipeline,
        "pca_pipeline": pca_pipeline,
        "rf_model": rf_pipeline
    }


def create_actual_vs_predicted_chart(
    y_test: np.ndarray,
    y_pred: np.ndarray,
    model_name: str = "PCA + Linear Regression"
) -> go.Figure:
    """Actual vs Predicted AQI scatter plot matching Notebook Step 10."""
    low = min(float(np.min(y_test)), float(np.min(y_pred)))
    high = max(float(np.max(y_test)), float(np.max(y_pred)))
    
    fig = go.Figure()
    
    # Observations scatter
    fig.add_trace(go.Scatter(
        x=y_test,
        y=y_pred,
        mode="markers",
        marker=dict(size=6, color="#2563eb", opacity=0.45),
        name="Predicted Observations"
    ))
    
    # Red ideal prediction diagonal line (y = x)
    fig.add_trace(go.Scatter(
        x=[low, high],
        y=[low, high],
        mode="lines",
        line=dict(color="#ef4444", width=2, dash="dash"),
        name="Ideal Prediction (y = x)"
    ))
    
    fig.update_layout(
        title=f"{model_name}: Actual vs. Predicted AQI",
        xaxis_title="Actual Ground-Truth AQI",
        yaxis_title="Predicted Model AQI",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    return style_figure(fig)


def create_pca_variance_chart(variance_ratios: List[float]) -> go.Figure:
    """PCA explained variance ratio per principal component."""
    labels = [f"PC {i+1}" for i in range(len(variance_ratios))]
    cumulative = np.cumsum(variance_ratios).round(2).tolist()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels,
        y=variance_ratios,
        name="Individual Variance (%)",
        marker_color="#3b82f6"
    ))
    fig.add_trace(go.Scatter(
        x=labels,
        y=cumulative,
        mode="lines+markers",
        name="Cumulative Variance (%)",
        line=dict(color="#ef4444", width=2)
    ))
    fig.update_layout(
        title=f"PCA Dimensionality Reduction: {len(variance_ratios)} Components (Total Variance: {cumulative[-1]}%)",
        xaxis_title="Principal Component",
        yaxis_title="Explained Variance Ratio (%)",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    return style_figure(fig)


def create_mini_gauge(aqi_value: float, category: str, color: str) -> go.Figure:
    """Create live AQI gauge chart for simulator."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(aqi_value, 1),
        title={"text": f"Predicted AQI — {category}", "font": {"size": 18, "color": "#0f172a"}},
        gauge={
            "axis": {"range": [0, 500], "tickwidth": 1, "tickcolor": "#64748b"},
            "bar": {"color": color, "thickness": 0.4},
            "steps": [
                {"range": [0, 50], "color": "#dcfce7"},
                {"range": [50, 100], "color": "#fef9c3"},
                {"range": [100, 200], "color": "#fef08a"},
                {"range": [200, 300], "color": "#fed7aa"},
                {"range": [300, 400], "color": "#fecaca"},
                {"range": [400, 500], "color": "#f3e8ff"}
            ]
        }
    ))
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=20))
    return style_figure(fig)


# Major Indian Urban Coordinates Reference Map (for auto-geocoding datasets with city names)
INDIAN_CITY_COORDINATES: Dict[str, Tuple[float, float]] = {
    "new delhi": (28.6139, 77.2090),
    "delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "kolkata": (22.5726, 88.3639),
    "hyderabad": (17.3850, 78.4867),
    "chennai": (13.0827, 80.2707),
    "pune": (18.5204, 73.8567),
    "ahmedabad": (23.0225, 72.5714),
    "jaipur": (26.9124, 75.7873),
    "lucknow": (26.8467, 80.9462),
    "kanpur": (26.4499, 80.3319),
    "nagpur": (21.1458, 79.0882),
    "indore": (22.7196, 75.8577),
    "thane": (19.2183, 72.9781),
    "bhopal": (23.2599, 77.4126),
    "visakhapatnam": (17.6868, 83.2185),
    "patna": (25.5941, 85.1376),
    "vadodara": (22.3072, 73.1812),
    "ghaziabad": (28.6692, 77.4538),
    "ludhiana": (30.9010, 75.8573),
    "agra": (27.1767, 78.0081),
    "nashik": (19.9975, 73.7898),
    "faridabad": (28.4089, 77.3178),
    "meerut": (28.9845, 77.7064),
    "rajkot": (22.3039, 70.8022),
    "varanasi": (25.3176, 82.9739),
    "srinagar": (34.0837, 74.7973),
    "amritsar": (31.6340, 74.8723),
    "chandigarh": (30.7333, 76.7794),
    "coimbatore": (11.0168, 76.9558),
    "kochi": (9.9312, 76.2673),
    "guwahati": (26.1445, 91.7362),
    "bhubaneswar": (20.2961, 85.8245),
    "ranchi": (23.3441, 85.3096),
    "howrah": (22.5958, 88.2636),
    "noida": (28.5355, 77.3910),
    "gurugram": (28.4595, 77.0266),
    "gurgaon": (28.4595, 77.0266)
}


def get_aqi_category_info(aqi_val: float) -> Tuple[str, str, str]:
    """Return category name, badge hex color, and health recommendation for an AQI value."""
    if aqi_val <= 50:
        return "Good", "#10b981", "Minimal impact. Safe for all outdoor activities."
    elif aqi_val <= 100:
        return "Satisfactory", "#84cc16", "Minor breathing discomfort to sensitive individuals."
    elif aqi_val <= 200:
        return "Moderate", "#eab308", "Breathing discomfort to sensitive groups; reduce prolonged exertion."
    elif aqi_val <= 300:
        return "Poor", "#f97316", "Breathing discomfort to most people. Wear masks outdoors."
    elif aqi_val <= 400:
        return "Very Poor", "#ef4444", "Respiratory illness likely on prolonged exposure. Avoid outdoors."
    else:
        return "Severe", "#7f1d1d", "Health emergency warning. High risk for everyone. Stay strictly indoors."


def extract_location_dataframe(df: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Extract, geocode, and aggregate location and monitoring station metrics from any dataset.
    Supports existing coordinates (latitude/longitude) or automatically geocodes known cities.
    """
    cols = {str(c).lower().strip(): c for c in df.columns}
    
    lat_col = next((cols[c] for c in ['latitude', 'lat', 'lat_deg', 'latitudes'] if c in cols), None)
    lon_col = next((cols[c] for c in ['longitude', 'lon', 'lng', 'long', 'lon_deg', 'longitudes'] if c in cols), None)
    loc_col = next((cols[c] for c in ['location', 'station', 'station_name', 'site', 'monitoring_station', 'area'] if c in cols), None)
    city_col = next((cols[c] for c in ['city', 'city_name', 'district', 'state'] if c in cols), None)
    
    work_df = df.copy()
    
    if lat_col and lon_col:
        work_df['__lat'] = pd.to_numeric(work_df[lat_col], errors='coerce')
        work_df['__lon'] = pd.to_numeric(work_df[lon_col], errors='coerce')
    elif city_col:
        def lookup_city(c):
            key = str(c).lower().strip()
            return INDIAN_CITY_COORDINATES.get(key, (np.nan, np.nan))
        coords = work_df[city_col].apply(lookup_city)
        work_df['__lat'] = [c[0] for c in coords]
        work_df['__lon'] = [c[1] for c in coords]
    elif loc_col:
        def lookup_loc(l):
            key = str(l).lower().strip()
            return INDIAN_CITY_COORDINATES.get(key, (np.nan, np.nan))
        coords = work_df[loc_col].apply(lookup_loc)
        work_df['__lat'] = [c[0] for c in coords]
        work_df['__lon'] = [c[1] for c in coords]
    else:
        return None, "No location, city, or coordinate columns found in the uploaded data."
        
    work_df = work_df.dropna(subset=['__lat', '__lon'])
    if work_df.empty:
        return None, "No valid geospatial coordinates could be extracted or geocoded."
        
    # Standardize location display names
    if loc_col and loc_col in work_df.columns:
        work_df['__station'] = work_df[loc_col].astype(str)
    elif city_col and city_col in work_df.columns:
        work_df['__station'] = work_df[city_col].astype(str)
    else:
        work_df['__station'] = "Station " + work_df.index.astype(str)
        
    if city_col and city_col in work_df.columns:
        work_df['__city'] = work_df[city_col].astype(str)
    else:
        work_df['__city'] = work_df['__station']
        
    # Ensure numeric columns
    numeric_targets = ['aqi', 'pm25', 'pm10', 'no2', 'so2', 'co', 'o3']
    for nt in numeric_targets:
        if nt in work_df.columns:
            work_df[nt] = pd.to_numeric(work_df[nt], errors='coerce')
            
    # If aqi not in columns, calculate approximation from PM2.5 / PM10 if possible
    if 'aqi' not in work_df.columns or work_df['aqi'].isna().all():
        if 'pm25' in work_df.columns and 'pm10' in work_df.columns:
            work_df['aqi'] = work_df['pm25'].fillna(0) * 1.5 + work_df['pm10'].fillna(0) * 0.5
        elif 'pm25' in work_df.columns:
            work_df['aqi'] = work_df['pm25'] * 2.0
        else:
            work_df['aqi'] = 100.0
            
    group_keys = ['__station', '__city', '__lat', '__lon']
    
    agg_spec = {
        'aqi': ('aqi', 'mean'),
        'record_count': ('aqi', 'count')
    }
    for pol in ['pm25', 'pm10', 'no2', 'so2', 'co', 'o3']:
        if pol in work_df.columns:
            agg_spec[pol] = (pol, 'mean')
            
    summary = work_df.groupby(group_keys, as_index=False).agg(**agg_spec)
    summary = summary.rename(columns={
        '__station': 'location',
        '__city': 'city',
        '__lat': 'latitude',
        '__lon': 'longitude'
    })
    
    # Round numerical metrics
    summary['aqi'] = summary['aqi'].round(1)
    for pol in ['pm25', 'pm10', 'no2', 'so2', 'o3']:
        if pol in summary.columns:
            summary[pol] = summary[pol].round(1)
    if 'co' in summary.columns:
        summary['co'] = summary['co'].round(2)
        
    # Assign category, badge color, and health advice
    cats, colors, advs = [], [], []
    for val in summary['aqi']:
        cat, col, adv = get_aqi_category_info(val)
        cats.append(cat)
        colors.append(col)
        advs.append(adv)
        
    summary['aqi_category'] = cats
    summary['category_color'] = colors
    summary['health_advisory'] = advs
    
    # Determine dominant pollutant for each station
    doms = []
    for _, row in summary.iterrows():
        p_vals = {}
        for p in ['pm25', 'pm10', 'no2', 'so2', 'co', 'o3']:
            if p in row and pd.notna(row[p]):
                p_vals[p] = row[p]
        if p_vals:
            dom = max(p_vals, key=p_vals.get).upper()
            doms.append(dom)
        else:
            doms.append("PM2.5")
    summary['dominant_pollutant'] = doms
    
    return summary, None


def create_geospatial_map(
    df: pd.DataFrame,
    metric: str = "aqi",
    selected_city: Optional[str] = None
) -> go.Figure:
    """
    Generate interactive geospatial map of monitoring stations across India using Plotly Scattergeo.
    Requires no external Mapbox tokens and runs 100% lightweight client-side.
    """
    summary, err = extract_location_dataframe(df)
    
    if summary is None or summary.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="📍 No Geospatial / Location Data Available in Current Dataset.<br><span style='font-size:12px;color:#64748b;'>Upload a CSV with 'latitude', 'longitude', 'location', or 'city' to view map.</span>",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=15, color="#475569")
        )
        fig.update_layout(height=480, margin=dict(l=20, r=20, t=40, b=20))
        return style_figure(fig)
        
    plot_df = summary.copy()
    if selected_city and selected_city != "ALL":
        filtered = plot_df[plot_df["city"].str.lower() == selected_city.lower()]
        if not filtered.empty:
            plot_df = filtered
            
    metric_col = metric.lower() if metric.lower() in plot_df.columns else "aqi"
    
    # Determine marker sizing (16 to 34 px)
    vals = plot_df[metric_col].fillna(0).values
    min_v, max_v = float(np.min(vals)), float(np.max(vals))
    if max_v > min_v:
        sizes = [16 + 18 * ((v - min_v) / (max_v - min_v)) for v in vals]
    else:
        sizes = [22] * len(vals)
        
    hover_texts = []
    for _, r in plot_df.iterrows():
        ht = (
            f"<b>📍 {r['location']}</b> ({r['city']})<br>"
            f"<b>AQI:</b> {r['aqi']} — <span style='color:{r['category_color']};font-weight:bold;'>{r['aqi_category']}</span><br>"
        )
        if 'pm25' in r and pd.notna(r['pm25']):
            ht += f"PM2.5: {r['pm25']} µg/m³ | "
        if 'pm10' in r and pd.notna(r['pm10']):
            ht += f"PM10: {r['pm10']} µg/m³<br>"
        if 'no2' in r and pd.notna(r['no2']):
            ht += f"NO2: {r['no2']} µg/m³ | "
        if 'co' in r and pd.notna(r['co']):
            ht += f"CO: {r['co']} mg/m³<br>"
        ht += (
            f"<b>Coordinates:</b> {r['latitude']:.4f}° N, {r['longitude']:.4f}° E<br>"
            f"<b>Observations:</b> {int(r['record_count']):,} records"
        )
        hover_texts.append(ht)
        
    fig = go.Figure()
    
    # Add station markers
    fig.add_trace(go.Scattergeo(
        lat=plot_df["latitude"],
        lon=plot_df["longitude"],
        text=plot_df["location"],
        hovertext=hover_texts,
        hoverinfo="text",
        mode="markers+text",
        textposition="top center",
        textfont=dict(size=11, color="#1e293b", family="sans-serif"),
        marker=dict(
            size=sizes,
            color=plot_df["category_color"],
            opacity=0.90,
            line=dict(width=2, color="#ffffff"),
            symbol="circle"
        ),
        name="Monitoring Stations"
    ))
    
    # Calculate map center based on filtered data
    center_lat = float(plot_df["latitude"].mean()) if not plot_df.empty else 21.5
    center_lon = float(plot_df["longitude"].mean()) if not plot_df.empty else 79.0
    scale = 8.5 if len(plot_df) <= 3 and (selected_city and selected_city != "ALL") else 4.3
    
    fig.update_geos(
        scope="asia",
        center=dict(lat=center_lat, lon=center_lon),
        projection_scale=scale,
        showland=True,
        landcolor="#f8fafc",
        countrycolor="#cbd5e1",
        coastlinecolor="#94a3b8",
        showsubunits=True,
        subunitcolor="#e2e8f0",
        showocean=True,
        oceancolor="#f0f9ff",
        lakecolor="#e0f2fe",
        showlakes=True,
        fitbounds=False
    )
    
    fig.update_layout(
        title=f"Geospatial Air Quality Monitoring Network ({len(plot_df)} Active Stations Mapped)",
        height=540,
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return style_figure(fig)


def create_location_kpis(
    df: pd.DataFrame,
    selected_city: Optional[str] = None
) -> html.Div:
    """Generate executive metric cards for the geospatial section."""
    summary, _ = extract_location_dataframe(df)
    
    if summary is None or summary.empty:
        return html.Div(
            style={"padding": "16px", "background": "#f8fafc", "borderRadius": "8px", "border": "1px solid #e2e8f0", "color": "#64748b", "textAlign": "center"},
            children="No location metrics available."
        )
        
    plot_df = summary.copy()
    if selected_city and selected_city != "ALL":
        filtered = plot_df[plot_df["city"].str.lower() == selected_city.lower()]
        if not filtered.empty:
            plot_df = filtered
            
    total_stations = len(plot_df)
    unique_cities = plot_df["city"].nunique()
    
    worst_row = plot_df.sort_values(by="aqi", ascending=False).iloc[0]
    best_row = plot_df.sort_values(by="aqi", ascending=True).iloc[0]
    avg_aqi = round(float(plot_df["aqi"].mean()), 1)
    avg_cat, avg_color, _ = get_aqi_category_info(avg_aqi)
    
    cards = [
        html.Div(
            className="metric-card metric-card--blue",
            children=[
                html.Div(className="metric-header", children=[
                    html.Span("Monitored Stations", className="metric-label"),
                    html.Span("📍", className="metric-icon")
                ]),
                html.Div(f"{total_stations} Stations", className="metric-value"),
                html.Div(f"Across {unique_cities} Urban Centers", className="metric-trend")
            ]
        ),
        html.Div(
            className="metric-card metric-card--red",
            children=[
                html.Div(className="metric-header", children=[
                    html.Span("Highest AQI Hotspot", className="metric-label"),
                    html.Span("⚠️", className="metric-icon")
                ]),
                html.Div(f"{worst_row['aqi']} AQI", className="metric-value", style={"color": worst_row["category_color"]}),
                html.Div(f"{worst_row['location']} ({worst_row['city']})", className="metric-trend")
            ]
        ),
        html.Div(
            className="metric-card metric-card--green",
            children=[
                html.Div(className="metric-header", children=[
                    html.Span("Cleanest Monitored Site", className="metric-label"),
                    html.Span("🍃", className="metric-icon")
                ]),
                html.Div(f"{best_row['aqi']} AQI", className="metric-value", style={"color": best_row["category_color"]}),
                html.Div(f"{best_row['location']} ({best_row['city']})", className="metric-trend")
            ]
        ),
        html.Div(
            className="metric-card metric-card--yellow",
            children=[
                html.Div(className="metric-header", children=[
                    html.Span("Network Average AQI", className="metric-label"),
                    html.Span("📊", className="metric-icon")
                ]),
                html.Div(f"{avg_aqi}", className="metric-value", style={"color": avg_color}),
                html.Div(f"Overall Status: {avg_cat}", className="metric-trend")
            ]
        )
    ]
    
    return html.Div(
        className="metric-grid",
        style={"marginBottom": "20px"},
        children=cards
    )


def create_location_ranking_table(
    df: pd.DataFrame,
    selected_city: Optional[str] = None
) -> html.Div:
    """Generate ranked station leaderboard table from highest to cleanest AQI."""
    summary, err = extract_location_dataframe(df)
    
    if summary is None or summary.empty:
        return html.Div(
            style={
                "background": "#f8fafc",
                "border": "1px dashed #cbd5e1",
                "borderRadius": "8px",
                "padding": "24px",
                "textAlign": "center"
            },
            children=[
                html.Div("ℹ️", style={"fontSize": "2rem", "marginBottom": "8px"}),
                html.H4("No Geospatial Station Data Available", style={"color": "#1e293b", "margin": "0 0 8px 0"}),
                html.P(
                    "To generate the geospatial map and station rankings, ensure your dataset includes columns such as 'location', 'city', 'latitude', or 'longitude'.",
                    style={"color": "#64748b", "fontSize": "0.9rem", "margin": "0"}
                )
            ]
        )
        
    plot_df = summary.copy()
    if selected_city and selected_city != "ALL":
        filtered = plot_df[plot_df["city"].str.lower() == selected_city.lower()]
        if not filtered.empty:
            plot_df = filtered
            
    sorted_df = plot_df.sort_values(by="aqi", ascending=False).reset_index(drop=True)
    
    header_style = {
        "padding": "12px 16px",
        "textAlign": "left",
        "backgroundColor": "#f8fafc",
        "color": "#475569",
        "fontWeight": "600",
        "fontSize": "0.82rem",
        "textTransform": "uppercase",
        "letterSpacing": "0.05em",
        "borderBottom": "2px solid #e2e8f0"
    }
    
    rows = []
    for rank, (_, row) in enumerate(sorted_df.iterrows(), start=1):
        rank_badge_color = "#ef4444" if rank <= 3 else ("#eab308" if rank <= 8 else "#10b981")
        
        row_children = [
            # Rank
            html.Td(
                html.Span(
                    f"#{rank}",
                    style={
                        "backgroundColor": rank_badge_color,
                        "color": "#ffffff",
                        "padding": "3px 8px",
                        "borderRadius": "12px",
                        "fontSize": "0.75rem",
                        "fontWeight": "700"
                    }
                ),
                style={"padding": "12px 16px", "width": "60px"}
            ),
            # Station Name
            html.Td(
                html.Div([
                    html.Span("📍 ", style={"fontSize": "0.85rem"}),
                    html.B(row["location"], style={"color": "#0f172a"})
                ]),
                style={"padding": "12px 16px"}
            ),
            # City
            html.Td(
                html.Span(
                    row["city"],
                    style={
                        "backgroundColor": "#e2e8f0",
                        "color": "#334155",
                        "padding": "3px 10px",
                        "borderRadius": "4px",
                        "fontSize": "0.8rem",
                        "fontWeight": "600"
                    }
                ),
                style={"padding": "12px 16px"}
            ),
            # Coordinates
            html.Td(
                html.Span(
                    f"{row['latitude']:.3f}° N, {row['longitude']:.3f}° E",
                    style={"color": "#64748b", "fontSize": "0.82rem", "fontFamily": "monospace"}
                ),
                style={"padding": "12px 16px"}
            ),
            # Average AQI
            html.Td(
                html.Span(
                    f"{row['aqi']:.1f}",
                    style={
                        "color": row["category_color"],
                        "fontWeight": "800",
                        "fontSize": "1.05rem"
                    }
                ),
                style={"padding": "12px 16px"}
            ),
            # CPCB Category
            html.Td(
                html.Span(
                    row["aqi_category"],
                    style={
                        "backgroundColor": f"{row['category_color']}18",
                        "color": row["category_color"],
                        "border": f"1px solid {row['category_color']}40",
                        "padding": "4px 10px",
                        "borderRadius": "16px",
                        "fontSize": "0.78rem",
                        "fontWeight": "700"
                    }
                ),
                style={"padding": "12px 16px"}
            ),
            # Dominant Pollutant
            html.Td(
                html.Span(
                    row["dominant_pollutant"],
                    style={
                        "backgroundColor": "#f1f5f9",
                        "color": "#0f172a",
                        "padding": "2px 8px",
                        "borderRadius": "4px",
                        "fontSize": "0.78rem",
                        "fontWeight": "700"
                    }
                ),
                style={"padding": "12px 16px"}
            ),
            # Records
            html.Td(
                html.Span(
                    f"{int(row['record_count']):,}",
                    style={"color": "#64748b", "fontSize": "0.85rem"}
                ),
                style={"padding": "12px 16px"}
            ),
            # Health Advisory
            html.Td(
                html.Span(
                    row["health_advisory"],
                    style={"color": "#334155", "fontSize": "0.83rem", "lineHeight": "1.4"}
                ),
                style={"padding": "12px 16px", "maxWidth": "280px"}
            )
        ]
        
        rows.append(
            html.Tr(
                row_children,
                style={
                    "borderBottom": "1px solid #f1f5f9",
                    "backgroundColor": "#ffffff" if rank % 2 == 1 else "#fafafa",
                    "transition": "background-color 0.2s"
                }
            )
        )
        
    table = html.Table(
        style={
            "width": "100%",
            "borderCollapse": "collapse",
            "fontSize": "0.88rem"
        },
        children=[
            html.Thead(
                html.Tr([
                    html.Th("Rank", style=header_style),
                    html.Th("Monitoring Location", style=header_style),
                    html.Th("City", style=header_style),
                    html.Th("Coordinates", style=header_style),
                    html.Th("Mean AQI", style=header_style),
                    html.Th("Status", style=header_style),
                    html.Th("Primary Pollutant", style=header_style),
                    html.Th("Readings", style=header_style),
                    html.Th("Health Advisory", style=header_style),
                ])
            ),
            html.Tbody(rows)
        ]
    )
    
    return html.Div(
        style={
            "overflowX": "auto",
            "borderRadius": "8px",
            "border": "1px solid #e2e8f0",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.05)"
        },
        children=[table]
    )

