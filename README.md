# Air Quality Monitoring System

An industry-level, real-time air quality monitoring platform with advanced data pipeline, interactive dashboard, and REST API.

## Features

### Core Capabilities
- **Real-time Data Collection**: Automated data ingestion from OpenAQ API with rate limiting and retry logic
- **Interactive Dashboard**: Modern Dash-based dashboard with live visualizations and auto-refresh
- **REST API**: Comprehensive API for external integrations and data access
- **WebSocket Support**: Real-time data streaming to connected clients
- **Multi-format Export**: Export data in CSV, JSON, Excel, or Parquet formats
- **Location Management**: Full CRUD operations for sensor locations
- **Data Quality**: Automated quality scoring and validation
- **Scalable Architecture**: Modular design supporting horizontal scaling

### Technical Highlights
- **Error Handling**: Exponential backoff retry logic for API calls
- **Structured Logging**: JSON-formatted logs with configurable levels
- **Configuration Management**: Environment-based configuration with Pydantic
- **Database**: DuckDB for analytics with optimized schemas
- **Caching**: Redis support for performance optimization
- **Authentication Ready**: Framework for JWT-based auth

## Architecture

```
air-quality-pipeline/
├── app/                          # Main application
│   ├── config/                   # Configuration management
│   ├── api/                      # REST API endpoints
│   ├── core/                     # Core business logic (database, cache)
│   ├── models/                   # Data models
│   ├── services/                 # Business services
│   ├── dashboard/                # Dashboard UI
│   ├── pipeline/                 # ETL Pipeline
│   │   ├── extractors/           # Data extractors
│   │   ├── transformers/         # Data transformers
│   │   └── loaders/              # Data loaders
│   ├── utils/                    # Utilities
│   └── websocket/                # WebSocket manager
├── scripts/                      # Utility scripts
├── tests/                        # Test suite
└── docs/                         # Documentation
```

## Quick Start

### Prerequisites
- Python 3.8+
- Redis (optional, for caching)
- OpenAQ API key

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd air-quality-pipeline
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Initialize database**
```bash
python scripts/setup_db.py
```

5. **Seed locations**
```bash
python scripts/seed_locations.py
```

6. **Collect initial data**
```bash
python scripts/collect_data.py
```

7. **Run the dashboard**
```bash
python app/main.py dashboard
```

Visit `http://localhost:8050` to access the dashboard.

## Usage

### Running the Application

**Dashboard only:**
```bash
python app/main.py dashboard
```

**Run full pipeline:**
```bash
python app/main.py pipeline
```

**Sync locations:**
```bash
python app/main.py sync-locations
```

**Collect measurements:**
```bash
python app/main.py collect-measurements
```

**With specific locations:**
```bash
python app/main.py collect-measurements --location-ids 123 456 789
```

**Debug mode:**
```bash
python app/main.py dashboard --debug
```

### Location Management

**List all locations:**
```bash
python scripts/manage_locations.py list
```

**Search locations:**
```bash
python scripts/manage_locations.py search "London"
```

**Sync from OpenAQ:**
```bash
python scripts/manage_locations.py sync --country US --limit 500
```

**View location statistics:**
```bash
python scripts/manage_locations.py stats 12345
```

**Activate/Deactivate location:**
```bash
python scripts/manage_locations.py activate 12345
python scripts/manage_locations.py deactivate 12345
```

### API Usage

**Start API server:**
```bash
uvicorn app.api.app:api_app --host 0.0.0.0 --port 8000
```

**API Endpoints:**
- `GET /api/v1/health` - Health check
- `GET /api/v1/locations` - List all locations
- `GET /api/v1/locations/{id}` - Get specific location
- `GET /api/v1/measurements/latest` - Get latest measurements
- `GET /api/v1/measurements/daily` - Get daily aggregates
- `POST /api/v1/export` - Export data
- `POST /api/v1/pipeline/sync` - Trigger pipeline sync
- `WS /api/v1/ws/{client_id}` - WebSocket connection

**Example API calls:**
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Get locations
curl http://localhost:8000/api/v1/locations

# Get latest measurements
curl http://localhost:8000/api/v1/measurements/latest?location_id=12345

# Export data
curl -X POST http://localhost:8000/api/v1/export \
  -H "Content-Type: application/json" \
  -d '{"format": "csv", "location_id": 12345}' \
  --output export.csv
```

## Configuration

Key environment variables in `.env`:

```bash
# Application
APP_NAME=Air Quality Monitoring System
DEBUG=false
ENVIRONMENT=development

# Server
HOST=0.0.0.0
PORT=8050
API_PORT=8000

# Database
DATABASE_PATH=data/air_quality.db

# OpenAQ API
OPENAQ_API_KEY=your_api_key_here
OPENAQ_RATE_LIMIT=10
OPENAQ_TIMEOUT=30

# Dashboard
DASH_REFRESH_INTERVAL=300

# Export
EXPORT_MAX_ROWS=100000
EXPORT_TEMP_DIR=temp/exports

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Data Pipeline

The ETL pipeline consists of three stages:

1. **Extract**: Fetch data from OpenAQ API with rate limiting
2. **Transform**: Apply quality checks and validation
3. **Load**: Store in DuckDB with optimized schemas

**Run pipeline manually:**
```bash
python app/main.py pipeline
```

**Pipeline features:**
- Automatic retry with exponential backoff
- Data quality scoring
- Duplicate detection
- Batch processing
- Error logging

## Dashboard Features

- **Live Map**: Interactive map with sensor locations and real-time readings
- **Trend Analysis**: Historical data visualization with line and box plots
- **Data Quality**: Quality metrics and statistics
- **Export**: Download data in multiple formats
- **Auto-refresh**: Configurable refresh intervals
- **Responsive Design**: Works on desktop, tablet, and mobile

## Monitoring & Logging

Logs are written to the `logs/` directory in JSON format:

```bash
# View logs
tail -f logs/app.log

# Filter logs
jq '.level == "ERROR"' logs/app.log
```

## Development

### Running Tests

```bash
pytest tests/
pytest tests/unit/
pytest tests/integration/
```

### Code Structure

- **config/**: Application settings and logging
- **core/**: Database, cache, and core utilities
- **services/**: Business logic (location, export, etc.)
- **pipeline/**: ETL extractors, transformers, loaders
- **dashboard/**: Dash app components and callbacks
- **api/**: FastAPI routes and schemas

## Deployment

### Production Deployment

1. **Set environment variables**
```bash
export ENVIRONMENT=production
export DEBUG=false
export SECRET_KEY=<your-secret-key>
```

2. **Use production WSGI server**
```bash
gunicorn app.dashboard.app:server -w 4 -k gevent -b 0.0.0.0:8050
```

3. **Run API server**
```bash
uvicorn app.api.app:api_app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Deployment (Coming Soon)

```bash
docker-compose up -d
```

## Troubleshooting

**Database connection errors:**
- Ensure `data/` directory exists
- Check `DATABASE_PATH` in `.env`

**API rate limiting:**
- Adjust `OPENAQ_RATE_LIMIT` in `.env`
- Check OpenAQ API key validity

**Memory issues:**
- Reduce `EXPORT_MAX_ROWS`
- Limit location count in collection

**Dashboard not loading:**
- Check browser console for errors
- Verify CSS files are in `app/dashboard/assets/css/`

## Performance Optimization

- Use Redis caching for frequently accessed data
- Implement materialized views for complex queries
- Batch process large datasets
- Use connection pooling
- Enable query caching in DuckDB

## Security Considerations

- Never commit `.env` files
- Use strong `SECRET_KEY` in production
- Implement rate limiting on API endpoints
- Enable HTTPS in production
- Regularly update dependencies
- Implement authentication (framework ready)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Check documentation in `docs/`
- Review logs in `logs/`
- Open an issue on GitHub

## Roadmap

- [ ] Complete authentication system
- [ ] Add Redis caching layer
- [ ] Implement automated testing
- [ ] Docker containerization
- [ ] Kubernetes deployment guides
- [ ] Alert system integration
- [ ] Mobile app
- [ ] Additional data sources
