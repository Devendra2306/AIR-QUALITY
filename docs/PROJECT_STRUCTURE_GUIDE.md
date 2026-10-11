# 📁 Complete Project Structure & Folder Guide

This document explains the purpose, architecture, and contents of **each and every directory and file** in the Air Quality Pipeline & Machine Learning project.

---

## 🌳 Directory Tree Overview

```
AIR-QUALITY-PIPELINE/
├── app/                     # Core application source code
│   ├── config/              # Environment settings and logging configuration
│   ├── core/                # Database connection and schema definitions (DuckDB)
│   ├── dashboard/           # Interactive Dash & Plotly web visualization app
│   │   ├── assets/css/      # Responsive stylesheets and modern dashboard theme
│   │   ├── callbacks/       # Interactivity logic (Map, Trends, ML, Export)
│   │   └── components/      # UI layouts, metric cards, charts, and ML panels
│   ├── ml/                  # Machine Learning core algorithms & AQI calculation
│   ├── pipeline/            # OpenAQ ETL data extraction, transformation, & loading
│   ├── services/            # Business logic (data export, location management)
│   ├── websocket/           # Real-time WebSocket connection manager
│   └── main.py              # Central entry point for CLI and Dashboard
├── data/                    # Analytical databases and datasets
│   ├── air_quality.db       # Embedded DuckDB database file
│   ├── raw_air_quality_data.csv # Raw uncleaned sensor dataset (for notebook)
│   └── sample_air_quality_dataset.csv # 3,000+ cleaned multi-city records
├── docker/                  # Docker containerization configuration files
├── docs/                    # Project documentation and presentation reports
│   ├── COLLEGE_PROJECT_REPORT.md # Academic report with architecture and viva Q&A
│   └── PROJECT_STRUCTURE_GUIDE.md# This folder-by-folder guide
├── logs/                    # Runtime system and error logs
├── models/                  # Serialized trained Machine Learning model artifacts
│   ├── aqi_model.joblib     # Production trained ML model
│   └── notebook_aqi_model.joblib # Model trained via Jupyter Notebook
├── notebooks/               # Jupyter interactive analysis notebooks
│   ├── Air_Quality_ML_Pipeline_and_Model_Training.ipynb # Complete step-by-step notebook
│   ├── api-exploration.ipynb# OpenAQ API testing and endpoint exploration
│   ├── data-quality-check.ipynb # Early data auditing experiments
│   └── s3-exploration.ipynb # Cloud object storage connection tests
├── scripts/                 # Standalone automation and utility scripts
│   ├── generate_raw_data.py # Generates raw uncleaned dataset with anomalies
│   ├── generate_sample_dataset.py # Generates 3,000+ records and seeds DuckDB
│   ├── train_model.py       # Standalone CLI ML model training script
│   ├── predict.py           # Standalone CLI real-time prediction script
│   ├── collect_data.py      # Trigger live OpenAQ API data extraction
│   ├── manage_locations.py  # Station metadata management
│   ├── mock_data.py         # Mock sensor data generator
│   ├── seed_locations.py    # Seeds monitoring station coordinates
│   └── setup_db.py          # Database schema initialization script
├── sql/                     # Raw SQL DDL and DML scripts
│   ├── ddl/                 # Schema and table definition scripts
│   └── dml/                 # View creations and analytical transformations
├── venv/                    # Active Python virtual environment (all dependencies)
├── .env                     # Local environment configuration file
├── .env.example             # Template for environment settings
├── .gitignore               # Git version control ignore rules
├── README.md                # Project landing page and quickstart guide
├── requirements.txt         # Pinned Python package dependencies
├── run.bat                  # One-click Windows interactive launcher menu
└── secrets.json             # API credentials placeholder
```

---

## 📂 Detailed Folder-by-Folder Guide

### 1. `app/` (Application Source Code)
The main application package containing all backend logic, database connections, ETL pipelines, machine learning models, and visualization dashboards.
* **`app/config/`**:
  - `settings.py`: Uses `pydantic-settings` to parse configuration variables (ports, database path, API keys, cache TTL) from `.env`.
  - `logging_config.py`: Sets up structured JSON logging for industry-standard audit trails.
* **`app/core/`**:
  - `database.py`: Manages the DuckDB embedded database connection. Automatically creates schemas (`raw`, `staging`, `presentation`, `analytics`) and manages connection context pooling.
* **`app/dashboard/`**:
  - `app.py`: The Dash application setup. Defines global layout tabs (Map View, Trends, ML & Visuals, Data Quality, Export) and initializes background callbacks.
  - `components/layout.py`: Reusable UI building blocks (Metric Cards, Headers, Panels, Loading Spinners).
  - `components/charts.py`: Plotly chart generators (Scatter Maps, Line Trends, Box Plots, Bar Charts).
  - `components/ml_layout.py`: Specialized UI layout for the Machine Learning tab, including file upload drag-and-drop, hyperparameter selectors, and the What-If prediction simulator.
  - `components/ml_charts.py`: Plotly charts for model evaluation (Actual vs. Predicted, Feature Importance, Residual Distributions, Correlation Heatmaps, AQI Gauge).
  - `callbacks/`: Event handlers that update charts dynamically when users click buttons, adjust sliders, or upload CSV files.
  - `assets/css/main.css`: Responsive CSS stylesheet providing styling for cards, buttons, tabs, and prediction gauges.
* **`app/ml/`**:
  - `aqi_calculator.py`: Implements official Indian CPCB / US EPA linear breakpoint interpolation formulas to calculate pollutant sub-indices, overall composite AQI, and health advisories.
  - `model_trainer.py`: Handles data preprocessing (`SimpleImputer`, `StandardScaler`), multi-algorithm training (Random Forest, Gradient Boosting, Linear Regression, Decision Trees), model evaluation ($R^2$, RMSE, MAE), feature importance extraction, and model saving/loading.
* **`app/pipeline/`**:
  - `extractors/`: Communicates with OpenAQ REST APIs to fetch real-world sensor measurements.
  - `transformers/`: Validates sensor readings against physical plausibility bounds and assigns data quality scores.
  - `loaders/`: Loads transformed batches into DuckDB tables and updates analytical views.
  - `orchestrator.py`: Orchestrates the complete pipeline cycle (Sync Locations -> Extract -> Transform -> Load -> Refresh Views).
* **`app/services/`**:
  - `export_service.py`: Converts database query results into downloadable CSV, JSON, Excel, and Parquet formats.
  - `location_service.py`: Helper functions for managing active monitoring stations.
* **`app/websocket/`**:
  - `manager.py`: Manages real-time WebSocket client connections for live sensor broadcasts.
* **`app/main.py`**:
  - The primary CLI entry point. Running `python app/main.py` launches the dashboard by default, or accepts subcommands (`train-model`, `generate-data`, `pipeline`).

---

### 2. `data/` (Storage & Datasets)
Contains database files and CSV datasets used by the project:
* **`air_quality.db`**: The embedded DuckDB columnar database containing thousands of partitioned sensor records.
* **`raw_air_quality_data.csv`**: Realistic **uncleaned** raw sensor dataset containing missing values, duplicates, mixed date formats, and negative sensor errors. Specifically created for step-by-step demonstration in Jupyter Notebook.
* **`sample_air_quality_dataset.csv`**: Comprehensive 3,000+ row multi-city dataset (Delhi, Mumbai, Bengaluru, Kolkata, Hyderabad) with pre-calculated AQI, used for model training and dashboard exploration.

---

### 3. `docker/` (Containerization)
Reserved for Docker configuration files (`Dockerfile`, `docker-compose.yml`) allowing one-command deployment across cloud servers or Linux containers without local dependency setup.

---

### 4. `docs/` (Project Documentation)
Contains documentation written for evaluators, college professors, and developers:
* **`COLLEGE_PROJECT_REPORT.md`**: Academic project report containing Problem Statement, System Architecture, Mathematical Formulations, Experimental Results Table, and **15 Viva Voce Questions & Answers**.
* **`PROJECT_STRUCTURE_GUIDE.md`**: (This file) Complete reference to every folder and file.

---

### 5. `logs/` (System & Error Logs)
Directory where system runtime logs, pipeline execution metrics, and error traces are stored for debugging and audit logging.

---

### 6. `models/` (Serialized ML Artifacts)
Stores trained machine learning model bundles serialized via `joblib`:
* **`aqi_model.joblib`**: Production model bundle (contains the trained Random Forest model, scaler, and feature mappings) used by the Dash dashboard and CLI scripts.
* **`notebook_aqi_model.joblib`**: Model artifact produced and saved directly by the Jupyter Notebook training workflow.

---

### 7. `notebooks/` (Jupyter Interactive Notebooks)
Houses Jupyter Notebooks demonstrating individual phases of the data science lifecycle:
* **`Air_Quality_ML_Pipeline_and_Model_Training.ipynb`**: The primary, pre-executed college project notebook featuring:
  - Step 1: Raw data loading
  - Step 2: Data cleaning (handling missing values, -999 noise, duplicates)
  - Step 3: Exploratory Data Analysis & Seaborn correlation heatmaps
  - Step 4: Mathematical AQI breakpoint calculation
  - Step 5: Training and comparing 4 ML models (Linear Regression, Decision Tree, Random Forest, Gradient Boosting)
  - Step 6: Model evaluation plots & feature importance
  - Step 7: Live prediction simulator function
* **`api-exploration.ipynb`**: Initial API testing for OpenAQ endpoints.
* **`data-quality-check.ipynb`**: Audit tests on sensor quality score algorithms.
* **`s3-exploration.ipynb`**: Prototype scripts for cloud data archiving.

---

### 8. `scripts/` (Automation & CLI Tools)
Standalone Python scripts for direct execution from the command line:
* **`train_model.py`**: Trains ML models on any custom CSV dataset or the database with terminal output:
  `python scripts/train_model.py --dataset data/sample_air_quality_dataset.csv --target aqi --algorithm random_forest`
* **`predict.py`**: CLI prediction tool that outputs predicted AQI and health advice:
  `python scripts/predict.py --pm25 55 --pm10 110 --no2 35 --so2 15 --co 1.0 --o3 30`
* **`generate_raw_data.py`**: Generates `data/raw_air_quality_data.csv` with realistic real-world flaws.
* **`generate_sample_dataset.py`**: Generates `data/sample_air_quality_dataset.csv` and seeds DuckDB with 8,000 measurements.
* **`setup_db.py`**: Initializes the DuckDB database schemas.
* **`collect_data.py`**: Fetches live data from OpenAQ API for active stations.
* **`manage_locations.py` & `seed_locations.py`**: Station metadata setup.

---

### 9. `sql/` (Database Queries)
Contains pure SQL scripts defining the analytical data warehouse:
* **`ddl/`**: Data Definition Language scripts creating schemas and base tables (`raw.measurements`, `staging.locations`).
* **`dml/`**: Data Manipulation Language scripts defining presentation views (`presentation.latest_measurements`, `presentation.daily_aggregates`).

---

### 10. `venv/` (Python Virtual Environment)
The self-contained Python 3 environment holding all installed project dependencies (`fastapi`, `duckdb`, `dash`, `plotly`, `scikit-learn`, `matplotlib`, `seaborn`, `jupyter`, `pandas`, `numpy`).

---

## 📄 Key Root Files

- **`run.bat`**: Interactive Windows batch script providing a 1-click launcher for the Web Dashboard, Jupyter Notebook, Model Training, and Prediction.
- **`README.md`**: Project overview, architecture diagrams, installation instructions, and quickstart commands.
- **`requirements.txt`**: List of all required Python packages and version constraints for reproducible setup.
- **`.env` / `.env.example`**: Configuration file storing application settings, database paths, and API keys.
- **`.gitignore`**: Specifies files that must not be tracked by Git (virtual environments, temporary caches, databases, `.env`).
- **`secrets.json`**: Optional credential storage for external API tokens.

---

## 🔄 How the Entire System Works Together

1. **Raw Ingestion:** Data is fetched via OpenAQ API (`app/pipeline/extractors/`) or loaded from CSV files (`data/raw_air_quality_data.csv`).
2. **Quality Transformation & Storage:** The pipeline checks values and saves records into **DuckDB** (`data/air_quality.db`).
3. **Machine Learning Training:** `app/ml/model_trainer.py` or the Jupyter Notebook loads data, cleans anomalies, standardizes values, and trains the ensemble **Random Forest** model, achieving $R^2 > 0.99$.
4. **Model Deployment:** The trained model is saved to `models/aqi_model.joblib`.
5. **Interactive Visualization:** The Dash application (`app/dashboard/app.py`) loads data from DuckDB and the trained ML model, rendering real-time maps, trend charts, feature importance rankings, and an interactive prediction simulator at `http://localhost:8050`.
