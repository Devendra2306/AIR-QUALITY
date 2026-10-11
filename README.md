# Real-Time Air Quality Monitoring & Machine Learning Pipeline

An industry-level, end-to-end air quality monitoring platform and machine learning predictive analytics system built for college minor projects and environmental data analysis.

It automatically ingests live and historical sensor data, processes it through an ETL pipeline into an embedded analytical database (**DuckDB**), trains **Machine Learning models** (Random Forest, Gradient Boosting, Linear Regression) to predict AQI and air severity categories, and visualizes everything on an interactive dashboard.

---

## 🌟 Key Features

- **End-to-End ETL Data Pipeline:** Ingestion, validation, quality scoring, and multi-schema loading (Raw, Staging, Presentation).
- **Embedded Columnar Database (DuckDB):** Ultra-fast analytical aggregations without external database server overhead.
- **Machine Learning & Predictive Engine:**
  - **Regression:** Predict continuous Air Quality Index (AQI), $PM_{2.5}$, or $PM_{10}$ with $R^2 > 0.99$.
  - **Classification:** Predict AQI severity categories (*Good, Satisfactory, Moderate, Poor, Very Poor, Severe*).
  - **Algorithms Supported:** Random Forest, Gradient Boosting, Linear/Ridge Regression, Decision Trees.
  - **Custom Dataset Support:** Train models directly by uploading **any CSV dataset** via web interface or CLI.
  - **Model Persistence:** Automated serialization and loading of trained models (`models/aqi_model.joblib`).
- **Interactive Visual Analytics Dashboard (Dash & Plotly):**
  - **Map View:** Interactive OpenStreetMap showing station readings.
  - **Trend Analysis:** Time-series trends and box-plot distributions.
  - **Machine Learning & Visuals Tab:**
    - Actual vs. Predicted scatter plot with 45° ideal fit line.
    - Feature Importance ranking chart.
    - Prediction error / residual distribution histogram.
    - Inter-pollutant correlation heatmap.
    - Real-Time "What-If" AQI Predictor with interactive gauge meter and health advisories.
  - **Data Export:** Export data to CSV, JSON, Excel, and Parquet.

---

## 🛠 Tech Stack

- **Core:** Python 3.10+
- **Data Engineering:** DuckDB, Pandas, NumPy, Polars
- **Machine Learning:** scikit-learn, joblib
- **Web Dashboard:** Dash, Plotly, HTML5, CSS3
- **Data Validation & Settings:** Pydantic

---

## 🚀 Quick Start (Running the Project)

### Option 1: 1-Click Launch on Windows
Double-click `run.bat` or run in terminal:
```cmd
.\run.bat
```

### Option 2: Running via Python
1. **Activate virtual environment:**
   ```bash
   .\venv\Scripts\activate
   ```

2. **Initialize Database & Seed Sample Data:**
   ```bash
   python scripts/generate_sample_dataset.py
   ```

3. **Launch the Dashboard:**
   ```bash
   python app/main.py dashboard
   ```
   Open your browser at: **`http://localhost:8050`**

---

## 🤖 Training the ML Model via CLI

You can train the model on any dataset directly from the terminal:

```bash
# Train Random Forest to predict AQI
python scripts/train_model.py --dataset data/sample_air_quality_dataset.csv --target aqi --algorithm random_forest

# Train to classify AQI Category
python scripts/train_model.py --dataset data/sample_air_quality_dataset.csv --target aqi_category --algorithm random_forest
```

---

## 🔮 Making Live Predictions via CLI

Predict AQI and view health advisories for custom pollutant values:

```bash
python scripts/predict.py --pm25 75.0 --pm10 140.0 --no2 50.0 --so2 18.0 --co 1.2 --o3 35.0
```

---

## 📚 College Project Documentation & Viva Voce Guide

Complete report covering system architecture, mathematical formulations, experimental results, and **15+ Viva Voce questions & model answers** is available in:
- **[`docs/COLLEGE_PROJECT_REPORT.md`](docs/COLLEGE_PROJECT_REPORT.md)**
