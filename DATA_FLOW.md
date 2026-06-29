# Air Quality Data Flow

## Current Batch Pipeline

1. Create the DuckDB schemas and raw table.

```powershell
python pipeline\database_manager.py --create --database-path air_quality.db --ddl-query-parent-dir sql\ddl
```

2. Extract monthly OpenAQ archive CSV files into `raw.air_quality`.

```powershell
python pipeline\extraction.py --locations_file_path location.json --start_date 2025-01 --end_date 2025-02 --database_path air_quality.db --extract_query_template_path sql\dml\raw\0_raw_air_quality_insert.sql --source_base_path s3://openaq-data-archive/records/csv.gz
```

3. Build the presentation views.

```powershell
python pipeline\transform.py --database-path air_quality.db --presentation-query-parent-dir sql\dml\presentation
```

4. Run the dashboard.

```powershell
python dashboard\app.py
```

## Live Data Path

The dashboard now refreshes from the local DuckDB file every five minutes. For live or near-live data, add a separate collector job that periodically pulls OpenAQ v3 latest measurements and inserts them into `raw.air_quality`, then lets the dashboard auto-refresh from the updated database.

Recommended flow:

```text
OpenAQ v3 latest API -> collector job -> DuckDB raw.air_quality -> presentation views -> Dash dashboard
```

Keep archive extraction for historical backfills, and use the API collector for current readings.

Run one live collection pass:

```powershell
python pipeline\live_collector.py --locations-file-path location.json --database-path air_quality.db
```

For testing a small subset:

```powershell
python pipeline\live_collector.py --locations-file-path location.json --database-path air_quality.db --max-locations 2 --dry-run
```

The collector reads the OpenAQ key from `OPENAQ_API_KEY` first, then from `secrets.json` using `openaq-api-key`.
