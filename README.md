# Air Quality Monitoring System

> **Note:** This project is currently a **Work In Progress (WIP) and remains incomplete**. The core pipeline and visualization components are functional, but several features are still under active development.

An industry-level, real-time air quality monitoring platform that collects data from the OpenAQ API, processes it through an ETL pipeline, and visualizes it on an interactive dashboard.

## Overview

Environmental data is often messy and fragmented. This project aims to automatically ingest live sensor data, clean it, and store it in an optimized analytical database (DuckDB) so it can be presented clearly on a live map and dashboard. 

## Tech Stack

- **Python** (Core language)
- **FastAPI** (REST API)
- **DuckDB** (Analytical database)
- **Dash & Plotly** (Interactive web dashboard)
- **Pydantic** (Data validation)

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd air-quality-pipeline
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Add your OpenAQ API key to .env
   ```

4. **Initialize and run:**
   ```bash
   # Setup database
   python scripts/setup_db.py
   
   # Run the dashboard
   python app/main.py dashboard
   ```

## Upcoming Features (Planned)

Since this project is still in development, the following features will be added in upcoming releases:

- **Docker Containerization**: Full Docker Compose setup for easy deployment.
- **Background Task Processing**: Integration with Celery and Redis to handle data extraction asynchronously.
- **Authentication**: A fully integrated JWT-based authentication system for API endpoints.
- **Enhanced Caching**: Redis caching layers to speed up dashboard load times for large datasets.
- **Alerting System**: Real-time alerts when AQI thresholds are breached.

## Contributing

Contributions are welcome! Since the project is in its early stages, feel free to open an issue to discuss proposed changes before submitting a pull request.

## License

MIT License
