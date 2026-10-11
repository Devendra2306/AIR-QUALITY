"""
Generate realistic RAW uncleaned air quality dataset for Jupyter Notebook demonstrations.
Includes real-world data issues: NaNs, outliers, duplicates, negative sensor errors,
mixed date formats, and uncalculated AQI.
"""

import random
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

output_path = Path("data/raw_air_quality_data.csv")
output_path.parent.mkdir(parents=True, exist_ok=True)

np.random.seed(101)
random.seed(101)

stations = [
    ("Anand Vihar", "Delhi"),
    ("Connaught Place", "Delhi"),
    ("Bandra Kurla Complex", "Mumbai"),
    ("Colaba", "Mumbai"),
    ("Whitefield", "Bengaluru"),
    ("Silk Board", "Bengaluru"),
    ("Victoria Memorial", "Kolkata"),
    ("Gachibowli", "Hyderabad"),
]

records = []
start = datetime(2024, 1, 1, 0, 0, 0)

for station, city in stations:
    current = start
    for _ in range(350):
        hour = current.hour
        # Diurnal rush hour effect
        rush = 1.35 if (8 <= hour <= 10 or 18 <= hour <= 21) else 0.85
        
        # Base realistic levels
        pm25 = max(5.0, round(35 * rush + random.uniform(-10, 25), 1))
        pm10 = max(10.0, round(pm25 * random.uniform(1.6, 2.1) + random.uniform(-5, 12), 1))
        no2 = max(4.0, round(28 * rush + random.uniform(-6, 15), 1))
        so2 = max(2.0, round(14 + random.uniform(-4, 9), 1))
        co = max(0.2, round(0.85 * rush + random.uniform(-0.15, 0.4), 2))
        o3 = max(5.0, round(32 + random.uniform(-8, 18), 1))
        temp = round(24 + 8 * np.sin((hour - 8) * np.pi / 12) + random.uniform(-2, 2), 1)
        humidity = round(np.clip(75 - (temp - 20) * 2.0 + random.uniform(-5, 5), 20, 95), 1)
        wind = round(random.uniform(2.0, 16.0), 1)
        
        # Inject realistic date formatting variations
        if random.random() < 0.2:
            dt_str = current.strftime("%Y/%m/%d %H:%M")
        else:
            dt_str = current.strftime("%Y-%m-%d %H:%M:%S")
            
        rec = {
            "Date_Time": dt_str,
            "Station_Name": station,
            "City": city,
            "PM2.5": pm25,
            "PM10": pm10,
            "NO2": no2,
            "SO2": so2,
            "CO": co,
            "O3": o3,
            "Temperature_C": temp,
            "Humidity_pct": humidity,
            "Wind_Speed_kmh": wind
        }
        
        # Inject realistic noise & missing values:
        # 1. Random NaNs in some readings (approx 3% of values)
        if random.random() < 0.03:
            rec["PM2.5"] = np.nan
        if random.random() < 0.03:
            rec["Temperature_C"] = np.nan
        if random.random() < 0.03:
            rec["NO2"] = np.nan
            
        # 2. Sensor error codes (e.g. -999 or -1) in approx 1% of readings
        if random.random() < 0.015:
            rec["PM10"] = -999.0
        if random.random() < 0.01:
            rec["CO"] = -1.0
            
        records.append(rec)
        current += timedelta(hours=3)

df = pd.DataFrame(records)

# 3. Inject duplicate rows (approx 15 duplicate rows)
duplicates = df.sample(15, random_state=42)
df = pd.concat([df, duplicates], ignore_index=True)

# Shuffle slightly to simulate realistic log ingestion
df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)

df.to_csv(output_path, index=False)
print(f"[OK] Generated RAW uncleaned dataset: {output_path} ({len(df)} rows)")
