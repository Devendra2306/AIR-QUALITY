import argparse
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from database_manager import close_database_connection, connect_to_database

OPENAQ_API_BASE_URL = "https://api.openaq.org/v3"

# Rate limiting configuration
DEFAULT_RATE_LIMIT = 10  # requests per second
RATE_LIMIT_WINDOW = 1.0  # seconds


def read_json(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_api_key(secrets_file_path: str | None) -> str:
    api_key = os.environ.get("OPENAQ_API_KEY")
    if api_key:
        return api_key

    if secrets_file_path and Path(secrets_file_path).exists():
        secrets = read_json(secrets_file_path)
        api_key = secrets.get("openaq-api-key")
        if api_key:
            return api_key

    raise RuntimeError(
        "OpenAQ API key not found. Set OPENAQ_API_KEY or provide secrets.json."
    )


def read_location_ids(location_file_path: str, requested_location_ids: list[int]) -> list[int]:
    if requested_location_ids:
        return requested_location_ids

    locations = read_json(location_file_path)
    return [int(location_id) for location_id in locations.keys()]


class RateLimiter:
    def __init__(self, max_calls: int = DEFAULT_RATE_LIMIT, window: float = RATE_LIMIT_WINDOW):
        self.max_calls = max_calls
        self.window = window
        self.calls = []
    
    def wait_if_needed(self):
        now = time.time()
        # Remove calls outside the window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.window]
        
        if len(self.calls) >= self.max_calls:
            sleep_time = self.window - (now - self.calls[0]) + 0.1
            if sleep_time > 0:
                time.sleep(sleep_time)
                self.calls = []
        
        self.calls.append(now)


def request_json(
    session: requests.Session,
    path: str,
    api_key: str,
    timeout_seconds: int,
    params: dict[str, Any] | None = None,
    rate_limiter: RateLimiter | None = None,
) -> dict[str, Any]:
    if rate_limiter:
        rate_limiter.wait_if_needed()
    
    response = session.get(
        f"{OPENAQ_API_BASE_URL}{path}",
        headers={"X-API-Key": api_key},
        params=params,
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


def fetch_location_metadata(
    session: requests.Session,
    location_id: int,
    api_key: str,
    timeout_seconds: int,
    rate_limiter: RateLimiter,
) -> dict[str, Any] | None:
    payload = request_json(
        session=session,
        path=f"/locations/{location_id}",
        api_key=api_key,
        timeout_seconds=timeout_seconds,
        rate_limiter=rate_limiter,
    )
    results = payload.get("results", [])
    if not results:
        return None
    return results[0]


def build_sensor_lookup(location_metadata: dict[str, Any]) -> dict[int, dict[str, str]]:
    sensor_lookup = {}

    for sensor in location_metadata.get("sensors", []):
        sensor_id = sensor.get("id")
        parameter = sensor.get("parameter", {})
        parameter_name = parameter.get("name") or sensor.get("name")
        units = parameter.get("units") or sensor.get("units")

        if sensor_id and parameter_name:
            sensor_lookup[int(sensor_id)] = {
                "parameter": str(parameter_name).lower(),
                "units": units or "",
            }

    return sensor_lookup


def fetch_latest_measurements(
    session: requests.Session,
    location_id: int,
    api_key: str,
    timeout_seconds: int,
    rate_limiter: RateLimiter,
) -> list[dict[str, Any]]:
    payload = request_json(
        session=session,
        path=f"/locations/{location_id}/latest",
        api_key=api_key,
        params={"limit": 100},
        timeout_seconds=timeout_seconds,
        rate_limiter=rate_limiter,
    )
    return payload.get("results", [])


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def measurement_to_row(
    measurement: dict[str, Any],
    location_metadata: dict[str, Any],
    sensor_lookup: dict[int, dict[str, str]],
) -> tuple[Any, ...] | None:
    sensor_id = measurement.get("sensorsId")
    location_id = measurement.get("locationsId")
    sensor = sensor_lookup.get(int(sensor_id)) if sensor_id else None

    if not sensor or not location_id:
        return None

    measured_at = parse_timestamp(measurement["datetime"]["utc"])
    coordinates = measurement.get("coordinates", {})
    latitude = coordinates.get("latitude")
    longitude = coordinates.get("longitude")
    ingestion_time = datetime.now(timezone.utc)

    return (
        int(location_id),
        int(sensor_id),
        location_metadata.get("name") or str(location_id),
        measured_at.replace(tzinfo=None),
        latitude,
        longitude,
        sensor["parameter"],
        sensor["units"],
        measurement.get("value"),
        int(location_id),
        str(measured_at.month).zfill(2),
        measured_at.year,
        ingestion_time.replace(tzinfo=None),
    )


def collect_latest_rows(
    location_ids: list[int],
    api_key: str,
    timeout_seconds: int,
    sleep_seconds: float,
    rate_limiter: RateLimiter,
) -> list[tuple[Any, ...]]:
    rows = []

    with requests.Session() as session:
        for location_id in location_ids:
            logging.info("Fetching latest measurements for location %s", location_id)
            metadata = fetch_location_metadata(
                session=session,
                location_id=location_id,
                api_key=api_key,
                timeout_seconds=timeout_seconds,
                rate_limiter=rate_limiter,
            )

            if not metadata:
                logging.warning("No metadata found for location %s", location_id)
                continue

            sensor_lookup = build_sensor_lookup(metadata)
            latest_measurements = fetch_latest_measurements(
                session=session,
                location_id=location_id,
                api_key=api_key,
                timeout_seconds=timeout_seconds,
                rate_limiter=rate_limiter,
            )

            for measurement in latest_measurements:
                row = measurement_to_row(measurement, metadata, sensor_lookup)
                if row:
                    rows.append(row)

            if sleep_seconds:
                time.sleep(sleep_seconds)

    return rows


def ensure_raw_table(con) -> None:
    # Create schema and table using SQL files
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute("""
        CREATE TABLE IF NOT EXISTS raw.air_quality (
            location_id BIGINT,
            sensors_id BIGINT,
            "location" VARCHAR,
            "datetime" TIMESTAMP,
            lat DOUBLE,
            lon DOUBLE,
            "parameter" VARCHAR,
            units VARCHAR,
            "value" DOUBLE,
            locationid BIGINT,
            "month" VARCHAR,
            "year" BIGINT,
            ingestion_datetime TIMESTAMP
        )
    """)


def insert_live_rows(database_path: str, rows: list[tuple[Any, ...]]) -> int:
    if not rows:
        return 0

    con = connect_to_database(database_path)
    try:
        ensure_raw_table(con)
        before_count = con.execute("SELECT COUNT(*) FROM raw.air_quality").fetchone()[0]
        con.execute("CREATE TEMP TABLE live_air_quality_stage AS SELECT * FROM raw.air_quality WHERE 1 = 0")
        con.executemany(
            """
            INSERT INTO live_air_quality_stage VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            rows,
        )
        con.execute(
            """
            INSERT INTO raw.air_quality
            SELECT stage.*
            FROM live_air_quality_stage AS stage
            WHERE NOT EXISTS (
                SELECT 1
                FROM raw.air_quality AS raw
                WHERE raw.location_id = stage.location_id
                  AND raw.sensors_id = stage.sensors_id
                  AND raw."datetime" = stage."datetime"
                  AND raw."parameter" = stage."parameter"
            )
            """
        )
        after_count = con.execute("SELECT COUNT(*) FROM raw.air_quality").fetchone()[0]
        return after_count - before_count
    finally:
        close_database_connection(con)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")

    parser = argparse.ArgumentParser(description="Collect latest OpenAQ readings.")
    parser.add_argument("--locations-file-path", default="location.json")
    parser.add_argument("--database-path", default="air_quality.db")
    parser.add_argument("--secrets-file-path", default="secrets.json")
    parser.add_argument("--location-id", action="append", type=int, default=[])
    parser.add_argument("--max-locations", type=int, default=None)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--sleep-seconds", type=float, default=0.25)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--rate-limit", type=int, default=DEFAULT_RATE_LIMIT, help="Max API calls per second")

    args = parser.parse_args()

    api_key = read_api_key(args.secrets_file_path)
    location_ids = read_location_ids(args.locations_file_path, args.location_id)

    if args.max_locations:
        location_ids = location_ids[: args.max_locations]

    rate_limiter = RateLimiter(max_calls=args.rate_limit)
    rows = collect_latest_rows(
        location_ids=location_ids,
        api_key=api_key,
        timeout_seconds=args.timeout_seconds,
        sleep_seconds=args.sleep_seconds,
        rate_limiter=rate_limiter,
    )

    if args.dry_run:
        logging.info("Dry run collected %s rows.", len(rows))
        return

    inserted_count = insert_live_rows(args.database_path, rows)
    logging.info("Collected %s rows; inserted %s new rows.", len(rows), inserted_count)


if __name__ == "__main__":
    main()
