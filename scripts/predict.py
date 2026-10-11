"""
Command-Line Air Quality & AQI Prediction Script
Make real-time predictions using the trained machine learning model.

Usage:
    python scripts/predict.py --pm25 45 --pm10 90 --no2 28 --so2 14 --co 0.9 --o3 32
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ml.model_trainer import ml_trainer
from app.ml.aqi_calculator import calculate_overall_aqi, get_aqi_category_info


def main():
    parser = argparse.ArgumentParser(
        description="Air Quality Real-Time Predictor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python scripts/predict.py --pm25 65.0 --pm10 120.0 --no2 45.0 --so2 18.0 --co 1.2 --o3 35.0 --temp 30.0 --humidity 55.0
        """
    )
    
    parser.add_argument("--pm25", type=float, default=45.0, help="PM2.5 concentration in µg/m³ (default: 45.0)")
    parser.add_argument("--pm10", type=float, default=85.0, help="PM10 concentration in µg/m³ (default: 85.0)")
    parser.add_argument("--no2", type=float, default=28.0, help="NO2 concentration in µg/m³ (default: 28.0)")
    parser.add_argument("--so2", type=float, default=14.0, help="SO2 concentration in µg/m³ (default: 14.0)")
    parser.add_argument("--co", type=float, default=0.9, help="CO concentration in ppm (default: 0.9)")
    parser.add_argument("--o3", type=float, default=32.0, help="Ozone concentration in µg/m³ (default: 32.0)")
    parser.add_argument("--temp", type=float, default=26.5, help="Ambient temperature in °C (default: 26.5)")
    parser.add_argument("--humidity", type=float, default=65.0, help="Relative humidity in %% (default: 65.0)")
    parser.add_argument("--wind", type=float, default=8.5, help="Wind speed in km/h (default: 8.5)")
    
    args = parser.parse_args()
    
    inputs = {
        "pm25": args.pm25,
        "pm10": args.pm10,
        "no2": args.no2,
        "so2": args.so2,
        "co": args.co,
        "o3": args.o3,
        "temperature": args.temp,
        "humidity": args.humidity,
        "wind_speed": args.wind
    }
    
    print("=" * 60)
    print("      AIR QUALITY INDEX (AQI) - PREDICTION ENGINE")
    print("=" * 60)
    print("INPUT CONCENTRATIONS:")
    for k, v in inputs.items():
        print(f"  - {k.upper():<14}: {v}")
        
    print("\n" + "-" * 60)
    
    try:
        pred_res = ml_trainer.predict_single(inputs)
        val = pred_res["predicted_value"]
        cat = pred_res["category"]
        advice = pred_res["advice"]
        print(f"[+] ML MODEL PREDICTION:")
        print(f"    Target AQI Value:  {val}")
        print(f"    Category:          {cat}")
        print(f"    Health Advisory:   {advice}")
    except Exception as e:
        print(f"[*] Fallback to EPA/NAQI Formula Calculator: ({e})")
        val, dom, cat, color = calculate_overall_aqi(inputs)
        adv = get_aqi_category_info(val)["advice"]
        print(f"    Calculated AQI:    {val}")
        print(f"    Dominant Element:  {dom.upper()}")
        print(f"    Category:          {cat}")
        print(f"    Health Advisory:   {adv}")
        
    print("=" * 60)


if __name__ == "__main__":
    main()
