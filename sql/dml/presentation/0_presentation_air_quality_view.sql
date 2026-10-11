CREATE OR REPLACE VIEW presentation.air_quality AS
SELECT
    location_id,
    sensors_id,
    "location",
    "datetime",
    lat,
    lon,
    "parameter",
    units,
    "value",
    locationid,
    "month",
    "year",
    ingestion_datetime
FROM raw.air_quality
WHERE "value" >= 0;
