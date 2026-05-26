CREATE OR REPLACE VIEW presentation.latest_param_values_per_location AS
WITH ranked_data AS (
    SELECT
        location_id,
        location,
        lat,
        lon,
        "parameter",
        "value",
        "datetime",
        ROW_NUMBER() OVER (
            PARTITION BY location_id, "parameter"
            ORDER BY "datetime" DESC
        ) AS rn
    FROM presentation.air_quality
    WHERE "parameter" IN ('pm10', 'pm25', 'so2')
),
latest_data AS (
    SELECT
        location_id,
        location,
        lat,
        lon,
        "parameter",
        "value",
        "datetime"
    FROM ranked_data
    WHERE rn = 1
)
SELECT
    location_id,
    location,
    MAX(lat) AS lat,
    MAX(lon) AS lon,
    MAX("datetime") AS "datetime",
    MAX(CASE WHEN "parameter" = 'pm10' THEN "value" END) AS pm10,
    MAX(CASE WHEN "parameter" = 'pm25' THEN "value" END) AS pm25,
    MAX(CASE WHEN "parameter" = 'so2' THEN "value" END) AS so2
FROM latest_data
GROUP BY
    location_id,
    location;
