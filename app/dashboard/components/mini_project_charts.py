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
