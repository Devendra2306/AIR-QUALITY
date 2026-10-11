"""
Standard Air Quality Index (AQI) Calculation Module
Based on standard Environmental Protection Agency & National Air Quality Index guidelines.
"""

from typing import Dict, Optional, Tuple, Any
import numpy as np
import pandas as pd


# Breakpoint tables for pollutants
# Format: (C_low, C_high, I_low, I_high)
BREAKPOINTS: Dict[str, list] = {
    "pm25": [
        (0.0, 30.0, 0, 50),
        (30.1, 60.0, 51, 100),
        (60.1, 90.0, 101, 200),
        (90.1, 120.0, 201, 300),
        (120.1, 250.0, 301, 400),
        (250.1, 500.0, 401, 500),
    ],
    "pm10": [
        (0.0, 50.0, 0, 50),
        (50.1, 100.0, 51, 100),
        (100.1, 250.0, 101, 200),
        (250.1, 350.0, 201, 300),
        (350.1, 430.0, 301, 400),
        (430.1, 600.0, 401, 500),
    ],
    "no2": [
        (0.0, 40.0, 0, 50),
        (40.1, 80.0, 51, 100),
        (80.1, 180.0, 101, 200),
        (180.1, 280.0, 201, 300),
        (280.1, 400.0, 301, 400),
        (400.1, 600.0, 401, 500),
    ],
    "so2": [
        (0.0, 40.0, 0, 50),
        (40.1, 80.0, 51, 100),
        (80.1, 380.0, 101, 200),
        (380.1, 800.0, 201, 300),
        (800.1, 1600.0, 301, 400),
        (1600.1, 2400.0, 401, 500),
    ],
    "co": [
        (0.0, 1.0, 0, 50),
        (1.1, 2.0, 51, 100),
        (2.1, 10.0, 101, 200),
        (10.1, 17.0, 201, 300),
        (17.1, 34.0, 301, 400),
        (34.1, 50.0, 401, 500),
    ],
    "o3": [
        (0.0, 50.0, 0, 50),
        (50.1, 100.0, 51, 100),
        (100.1, 168.0, 101, 200),
        (168.1, 208.0, 201, 300),
        (208.1, 748.0, 301, 400),
        (748.1, 1000.0, 401, 500),
    ],
}


CATEGORIES = [
    (0, 50, "Good", "#10b981", "Air quality is considered satisfactory, and air pollution poses little or no risk."),
    (51, 100, "Satisfactory", "#3b82f6", "Air quality is acceptable; minor breathing discomfort to sensitive people."),
    (101, 200, "Moderate", "#f59e0b", "Breathing discomfort to people with lung, asthma and heart diseases."),
    (201, 300, "Poor", "#f97316", "Breathing discomfort to most people on prolonged exposure."),
    (301, 400, "Very Poor", "#ef4444", "Respiratory illness to the people on prolonged exposure."),
    (401, 9999, "Severe", "#7f1d1d", "Healthy people may experience respiratory effects; serious impacts for sensitive groups.")
]


def calculate_sub_index(parameter: str, concentration: float) -> Optional[float]:
    """Calculate sub-index for a single pollutant concentration using linear interpolation."""
    param_clean = parameter.lower().replace(".", "").replace("-", "").strip()
    if param_clean not in BREAKPOINTS or concentration is None or np.isnan(concentration) or concentration < 0:
        return None

    for c_low, c_high, i_low, i_high in BREAKPOINTS[param_clean]:
        if c_low <= concentration <= c_high:
            sub_index = ((i_high - i_low) / (c_high - c_low)) * (concentration - c_low) + i_low
            return round(sub_index, 2)
            
    # If concentration exceeds the highest breakpoint
    max_c_low, max_c_high, max_i_low, max_i_high = BREAKPOINTS[param_clean][-1]
    if concentration > max_c_high:
        sub_index = ((max_i_high - max_i_low) / (max_c_high - max_c_low)) * (concentration - max_c_low) + max_i_low
        return round(min(sub_index, 500.0), 2)
        
    return None


def get_aqi_category_info(aqi: float) -> Dict[str, Any]:
    """Get category name, color, and health message for a given AQI value."""
    if aqi is None or np.isnan(aqi):
        return {
            "category": "Unknown",
            "color": "#64748b",
            "advice": "No reliable data available."
        }
    
    for low, high, cat, color, advice in CATEGORIES:
        if low <= aqi <= high:
            return {
                "category": cat,
                "color": color,
                "advice": advice
            }
            
    return {
        "category": "Severe",
        "color": "#7f1d1d",
        "advice": "Emergency conditions. Health warnings of emergency conditions for entire population."
    }


def calculate_overall_aqi(pollutants: Dict[str, float]) -> Tuple[float, str, str, str]:
    """
    Calculate composite AQI from a dict of pollutant values.
    Returns: (aqi_value, dominant_pollutant, category, color)
    """
    sub_indices: Dict[str, float] = {}
    for param, val in pollutants.items():
        if val is not None and not np.isnan(val):
            sub = calculate_sub_index(param, float(val))
            if sub is not None:
                sub_indices[param.lower()] = sub
                
    if not sub_indices:
        return 0.0, "None", "Good", "#10b981"
        
    dominant_param = max(sub_indices, key=sub_indices.get)
    overall_aqi = round(sub_indices[dominant_param], 1)
    cat_info = get_aqi_category_info(overall_aqi)
    
    return overall_aqi, dominant_param, cat_info["category"], cat_info["color"]


def enrich_dataframe_with_aqi(df: pd.DataFrame) -> pd.DataFrame:
    """Enrich a dataframe with calculated AQI and Category columns if not present."""
    df_copy = df.copy()
    
    # Standardize column names to lowercase
    col_map = {c: c.lower().replace(".", "").replace("-", "").replace(" ", "_") for c in df_copy.columns}
    inv_map = {v: k for k, v in col_map.items()}
    
    # Check if aqi already exists
    has_aqi = any("aqi" == col_map[c] for c in df_copy.columns)
    
    pollutant_cols = ["pm25", "pm10", "no2", "so2", "co", "o3"]
    available_pollutants = [c for c in df_copy.columns if col_map[c] in pollutant_cols]
    
    if not has_aqi and available_pollutants:
        calculated_aqis = []
        dominant_params = []
        categories = []
        
        for _, row in df_copy.iterrows():
            pollutant_dict = {col_map[c]: row[c] for c in available_pollutants if pd.notna(row[c])}
            aqi, dom, cat, _ = calculate_overall_aqi(pollutant_dict)
            calculated_aqis.append(aqi)
            dominant_params.append(dom)
            categories.append(cat)
            
        df_copy["aqi"] = calculated_aqis
        df_copy["dominant_pollutant"] = dominant_params
        df_copy["aqi_category"] = categories
    elif has_aqi and "aqi_category" not in [col_map[c] for c in df_copy.columns]:
        aqi_col = [c for c in df_copy.columns if col_map[c] == "aqi"][0]
        df_copy["aqi_category"] = df_copy[aqi_col].apply(lambda x: get_aqi_category_info(x)["category"])
        
    return df_copy
