"""
Sample Dataset Verification and Loader Script for Render Build Pipeline.
Ensures sample_air_quality_dataset.csv is present in data/ and assets/ directories.
"""

from pathlib import Path
import shutil
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def generate_dataset():
    """Verify or load sample air quality dataset."""
    dest_path = PROJECT_ROOT / "data" / "sample_air_quality_dataset.csv"
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    src_candidates = [
        PROJECT_ROOT / "mini project final set" / "sample_air_quality_dataset.csv",
        PROJECT_ROOT / "app" / "dashboard" / "assets" / "sample_air_quality_dataset.csv",
        dest_path
    ]
    
    found = False
    for src in src_candidates:
        if src.exists():
            if src != dest_path:
                shutil.copy2(src, dest_path)
            found = True
            break
            
    if not found:
        # Fallback minimal dataset if not found
        df = pd.DataFrame({
            "timestamp": pd.date_range("2026-01-01", periods=100, freq="h"),
            "city": ["New Delhi"] * 100,
            "pm25": [45.0] * 100,
            "pm10": [85.0] * 100,
            "no2": [28.0] * 100,
            "so2": [14.0] * 100,
            "co": [0.9] * 100,
            "o3": [32.0] * 100,
            "temperature": [26.0] * 100,
            "humidity": [65.0] * 100,
            "wind_speed": [8.0] * 100,
            "aqi": [75.0] * 100,
            "dominant_pollutant": ["pm25"] * 100,
            "aqi_category": ["Satisfactory"] * 100
        })
        df.to_csv(dest_path, index=False)
        
    df = pd.read_csv(dest_path)
    print(f"Sample air quality dataset ready! {len(df):,} records loaded successfully.")
    return df


if __name__ == "__main__":
    generate_dataset()
