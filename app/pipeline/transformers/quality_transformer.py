from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from app.config.logging_config import logger


class QualityTransformer:
    """Transform raw data with quality checks and validation."""
    
    def __init__(self):
        self.quality_thresholds = {
            "pm25": {"min": 0, "max": 500},
            "pm10": {"min": 0, "max": 600},
            "no2": {"min": 0, "max": 200},
            "so2": {"min": 0, "max": 1000},
            "o3": {"min": 0, "max": 400},
            "co": {"min": 0, "max": 50},
        }
    
    def calculate_quality_score(self, parameter: str, value: float) -> float:
        """Calculate quality score based on parameter thresholds."""
        if parameter not in self.quality_thresholds:
            return 0.5  # Default score for unknown parameters
        
        thresholds = self.quality_thresholds[parameter]
        
        # Check if value is within valid range
        if value < thresholds["min"] or value > thresholds["max"]:
            return 0.0  # Invalid value
        
        # Calculate score based on AQI-like logic
        # Higher values = lower quality score
        range_size = thresholds["max"] - thresholds["min"]
        normalized = (value - thresholds["min"]) / range_size
        score = 1.0 - normalized
        
        return max(0.0, min(1.0, score))
    
    def detect_outliers(
        self,
        data: pd.DataFrame,
        parameter: str,
        method: str = "iqr"
    ) -> pd.Series:
        """Detect outliers using specified method."""
        if method == "iqr":
            Q1 = data[parameter].quantile(0.25)
            Q3 = data[parameter].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            return (data[parameter] < lower_bound) | (data[parameter] > upper_bound)
        elif method == "zscore":
            mean = data[parameter].mean()
            std = data[parameter].std()
            z_scores = abs((data[parameter] - mean) / std)
            return z_scores > 3
        else:
            raise ValueError(f"Unknown outlier detection method: {method}")
    
    def transform_measurements(
        self,
        raw_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform raw measurements with quality checks."""
        if not raw_data:
            return []
        
        df = pd.DataFrame(raw_data)
        
        # Standardize column names
        column_mapping = {
            "locationsId": "location_id",
            "sensorsId": "sensor_id",
            "location": "location_name",
            "coordinates": "coordinates",
            "parameter": "parameter",
            "value": "value",
            "unit": "unit",
            "datetime": "measurement_time",
        }
        df = df.rename(columns=column_mapping)
        
        # Extract coordinates
        if "coordinates" in df.columns:
            df["latitude"] = df["coordinates"].apply(
                lambda x: x.get("latitude") if isinstance(x, dict) else None
            )
            df["longitude"] = df["coordinates"].apply(
                lambda x: x.get("longitude") if isinstance(x, dict) else None
            )
        
        # Parse datetime
        if "measurement_time" in df.columns:
            df["measurement_time"] = pd.to_datetime(df["measurement_time"])
        
        # Calculate quality scores
        df["quality_score"] = df.apply(
            lambda row: self.calculate_quality_score(
                row.get("parameter", ""),
                row.get("value", 0)
            ),
            axis=1
        )
        
        # Add ingestion timestamp
        df["ingestion_time"] = datetime.now(timezone.utc)
        
        # Add source
        df["source"] = "openaq"
        
        # Filter out invalid records
        valid_records = df[
            (df["value"].notna()) &
            (df["value"] >= 0) &
            (df["quality_score"] > 0)
        ]
        
        logger.info(
            f"Transformed {len(raw_data)} records, "
            f"{len(valid_records)} valid, {len(raw_data) - len(valid_records)} filtered"
        )
        
        return valid_records.to_dict("records")
    
    def aggregate_to_hourly(
        self,
        data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Aggregate measurements to hourly averages."""
        if not data:
            return []
        
        df = pd.DataFrame(data)
        
        # Convert to datetime if needed
        if "measurement_time" in df.columns:
            df["measurement_time"] = pd.to_datetime(df["measurement_time"])
        
        # Create hour column
        df["hour"] = df["measurement_time"].dt.floor("H")
        
        # Group and aggregate
        aggregated = df.groupby(
            ["location_id", "parameter", "hour"]
        ).agg({
            "value": ["mean", "min", "max", "std", "count"],
            "quality_score": "mean",
            "latitude": "first",
            "longitude": "first",
            "unit": "first"
        }).reset_index()
        
        # Flatten column names
        aggregated.columns = [
            "location_id",
            "parameter",
            "hour",
            "avg_value",
            "min_value",
            "max_value",
            "std_value",
            "count",
            "avg_quality",
            "latitude",
            "longitude",
            "unit"
        ]
        
        logger.info(f"Aggregated to {len(aggregated)} hourly records")
        
        return aggregated.to_dict("records")
