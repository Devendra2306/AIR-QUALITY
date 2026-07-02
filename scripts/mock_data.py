import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import db_manager

def generate_mock_data():
    db_manager.initialize_schema()
    
    # Mock Locations for Mumbai
    locations = [
        (1, "Bandra Kurla Complex", "Mumbai", "IN", 19.0658, 72.8660, "Asia/Kolkata", True),
        (2, "Colaba", "Mumbai", "IN", 18.9150, 72.8258, "Asia/Kolkata", True),
        (3, "Andheri East", "Mumbai", "IN", 19.1136, 72.8697, "Asia/Kolkata", True),
        (4, "Borivali East", "Mumbai", "IN", 19.2307, 72.8567, "Asia/Kolkata", True),
    ]
    
    with db_manager.get_connection() as conn:
        conn.execute("DELETE FROM staging.locations")
        for loc in locations:
            conn.execute(
                "INSERT INTO staging.locations (location_id, name, city, country, latitude, longitude, timezone, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                loc
            )
        print("Mock locations inserted.")

    # Mock Measurements
    parameters = ["pm25", "pm10", "co", "no2", "o3", "temperature", "humidity"]
    units = {"pm25": "µg/m³", "pm10": "µg/m³", "co": "ppm", "no2": "ppm", "o3": "ppm", "temperature": "C", "humidity": "%"}
    
    now = datetime.now()
    
    with db_manager.get_connection() as conn:
        conn.execute("DELETE FROM raw.measurements")
        measurement_id = 1
        for loc in locations:
            loc_id = loc[0]
            loc_name = loc[1]
            lat = loc[4]
            lon = loc[5]
            
            # Generate past 24 hours of data
            for hours_ago in range(24, -1, -1):
                meas_time = now - timedelta(hours=hours_ago)
                for param in parameters:
                    val = random.uniform(5, 50)
                    if param == "temperature":
                        val = random.uniform(15, 30)
                    elif param == "humidity":
                        val = random.uniform(30, 80)
                        
                    conn.execute(
                        """
                        INSERT INTO raw.measurements 
                        (id, location_id, sensor_id, location, latitude, longitude, parameter, unit, value, measurement_time, source, quality_score) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (measurement_id, loc_id, measurement_id + 1000, loc_name, lat, lon, param, units[param], val, meas_time, "mock", 1.0)
                    )
                    measurement_id += 1
        print("Mock measurements inserted.")

if __name__ == "__main__":
    generate_mock_data()
