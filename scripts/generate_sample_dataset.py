"""
Air Quality Dataset Generator
Generates a realistic, comprehensive, multi-city Indian Air Quality dataset
with standard pollutants, meteorological variables, AQI, and classifications.
"""

import sys
from pathlib import Path
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ml.aqi_calculator import calculate_overall_aqi, get_aqi_category_info
from app.core.database import db_manager


CITIES = [
    {
        "city": "New Delhi",
        "stations": [
            ("Anand Vihar", 28.6502, 77.3150, 1.4),
            ("Connaught Place", 28.6315, 77.2167, 1.1),
            ("R.K. Puram", 28.5660, 77.1767, 1.25)
        ]
    },
    {
        "city": "Mumbai",
        "stations": [
            ("Bandra Kurla Complex", 19.0658, 72.8660, 1.0),
            ("Colaba", 18.9150, 72.8258, 0.75),
            ("Andheri East", 19.1136, 72.8697, 1.05)
        ]
    },
    {
        "city": "Bengaluru",
        "stations": [
            ("Silk Board", 12.9176, 77.6238, 0.85),
            ("Whitefield", 12.9698, 77.7500, 0.7),
            ("BTM Layout", 12.9165, 77.6101, 0.65)
        ]
    },
    {
        "city": "Kolkata",
        "stations": [
            ("Victoria Memorial", 22.5448, 88.3426, 0.95),
            ("Howrah", 22.5958, 88.2636, 1.2)
        ]
    },
    {
        "city": "Hyderabad",
        "stations": [
            ("Gachibowli", 17.4401, 78.3489, 0.75),
            ("Charminar", 17.3616, 78.4747, 1.0)
        ]
    }
]


def generate_dataset(num_days: int = 30, output_path: str = "data/sample_air_quality_dataset.csv") -> pd.DataFrame:
    """Generate realistic air quality dataset and save as CSV."""
    records = []
    
    start_date = datetime.now() - timedelta(days=num_days)
    np.random.seed(42)
    random.seed(42)
    
    for city_info in CITIES:
        city = city_info["city"]
        for station_name, lat, lon, city_factor in city_info["stations"]:
            # Generate measurements every 3 hours over num_days
            current_time = start_date
            while current_time <= datetime.now():
                hour = current_time.hour
                
                # Diurnal rush-hour effects (8-10 AM, 6-9 PM)
                is_rush_hour = 1.35 if (8 <= hour <= 10 or 18 <= hour <= 21) else 0.85
                
                # Temperature cycle (cooler at night, hotter in afternoon)
                temp = round(22 + 9 * np.sin((hour - 8) * np.pi / 12) + random.uniform(-2, 2), 1)
                humidity = round(np.clip(80 - (temp - 20) * 2.2 + random.uniform(-5, 5), 25, 95), 1)
                wind_speed = round(random.uniform(2.0, 18.0), 1)
                
                # Dispersion factor: high wind disperses pollution
                dispersion = np.clip(1.0 - (wind_speed - 5.0) * 0.03, 0.55, 1.3)
                
                # Base pollutant levels modulated by factors
                pm25 = max(5.0, round(
                    (35 * city_factor * is_rush_hour * dispersion) + random.uniform(-10, 25), 1
                ))
                pm10 = max(10.0, round(
                    (pm25 * random.uniform(1.6, 2.1)) + random.uniform(-5, 15), 1
                ))
                no2 = max(5.0, round(
                    (28 * city_factor * is_rush_hour) + random.uniform(-6, 12), 1
                ))
                so2 = max(3.0, round(
                    (15 * city_factor * dispersion) + random.uniform(-4, 8), 1
                ))
                co = max(0.2, round(
                    (0.8 * city_factor * is_rush_hour) + random.uniform(-0.1, 0.4), 2
                ))
                # Ozone is formed photochemically by sunlight, higher in mid-day
                o3 = max(5.0, round(
                    (30 * (1.0 + (temp / 35.0))) + random.uniform(-8, 15), 1
                ))
                
                # Compute AQI
                pollutants = {
                    "pm25": pm25,
                    "pm10": pm10,
                    "no2": no2,
                    "so2": so2,
                    "co": co,
                    "o3": o3
                }
                aqi, dominant, category, color = calculate_overall_aqi(pollutants)
                
                records.append({
                    "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "city": city,
                    "location": station_name,
                    "latitude": lat,
                    "longitude": lon,
                    "pm25": pm25,
                    "pm10": pm10,
                    "no2": no2,
                    "so2": so2,
                    "co": co,
                    "o3": o3,
                    "temperature": temp,
                    "humidity": humidity,
                    "wind_speed": wind_speed,
                    "aqi": aqi,
                    "dominant_pollutant": dominant,
                    "aqi_category": category
                })
                
                current_time += timedelta(hours=3)
                
    df = pd.DataFrame(records)
    
    # Save CSV
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"[OK] Generated {len(df)} records in {out_path}")
    return df


def seed_database_from_dataframe(df: pd.DataFrame):
    """Seed DuckDB database with the generated records for live map & trends."""
    db_manager.initialize_schema()
    
    # Unique locations
    unique_locs = df[["location", "city", "latitude", "longitude"]].drop_duplicates().reset_index(drop=True)
    
    with db_manager.get_connection() as conn:
        conn.execute("DELETE FROM staging.locations")
        conn.execute("DELETE FROM raw.measurements")
        
        loc_id_map = {}
        for idx, row in unique_locs.iterrows():
            loc_id = idx + 1
            loc_id_map[row["location"]] = loc_id
            conn.execute(
                """
                INSERT INTO staging.locations 
                (location_id, name, city, country, latitude, longitude, timezone, is_active)
                VALUES (?, ?, ?, 'IN', ?, ?, 'Asia/Kolkata', TRUE)
                """,
                (loc_id, row["location"], row["city"], row["latitude"], row["longitude"])
            )
            
        # Insert measurements
        meas_id = 1
        param_units = {
            "pm25": "µg/m³",
            "pm10": "µg/m³",
            "no2": "µg/m³",
            "so2": "µg/m³",
            "co": "ppm",
            "o3": "µg/m³",
            "temperature": "°C",
            "humidity": "%"
        }
        
        # Take latest 500 rows for DB
        subset = df.tail(1000)
        for _, row in subset.iterrows():
            loc_id = loc_id_map[row["location"]]
            m_time = pd.to_datetime(row["timestamp"])
            
            for param, unit in param_units.items():
                val = row.get(param)
                if pd.notna(val):
                    conn.execute(
                        """
                        INSERT INTO raw.measurements
                        (id, location_id, sensor_id, location, latitude, longitude, parameter, unit, value, measurement_time, source, quality_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'sensor_feed', 1.0)
                        """,
                        (meas_id, loc_id, meas_id + 5000, row["location"], row["latitude"], row["longitude"], param, unit, float(val), m_time)
                    )
                    meas_id += 1
                    
    # Recreate presentation views
    from app.pipeline.orchestrator import PipelineOrchestrator
    PipelineOrchestrator()._create_presentation_views()
    print(f"[OK] Seeded {meas_id - 1} measurements into DuckDB database.")


if __name__ == "__main__":
    df = generate_dataset()
    seed_database_from_dataframe(df)
