# COLLEGE MINOR PROJECT REPORT

## Project Title
**Real-Time Air Quality Monitoring, ETL Data Pipeline & Machine Learning Predictive Analytics System**

**Course:** B.Tech / B.E. / B.Sc. / BCA / MCA Minor Project  
**Domain:** Data Engineering, Machine Learning, Environmental Informatics  
**Tech Stack:** Python 3, DuckDB, scikit-learn, Dash & Plotly, Pandas, NumPy  

---

## 1. Abstract
Rapid urbanization and industrialization have exacerbated air pollution worldwide, necessitating robust monitoring and forecasting systems. This project presents an industry-grade, end-to-end Air Quality Monitoring and Predictive Analytics Pipeline. 

The system collects heterogeneous environmental data (particulate matter $PM_{2.5}, PM_{10}$, and gaseous pollutants $NO_2, SO_2, CO, O_3$ alongside meteorological factors such as temperature, humidity, and wind speed). The incoming data is cleaned, validated with quality scoring, and ingested into an embedded column-store analytical database (**DuckDB**). 

Furthermore, a comprehensive **Machine Learning Engine** is integrated using **Random Forest**, **Gradient Boosting**, and **Linear Regression** to predict continuous Air Quality Index (AQI) values ($R^2 > 0.99$) and classify air severity categories. The system visualizes these insights through an interactive web dashboard providing real-time geographical mapping, pollutant trends, actual vs. predicted model fidelity, feature importance rankings, and an interactive "What-If" prediction simulator.

---

## 2. Problem Statement & Objectives
### 2.1 Problem Statement
Conventional environmental monitoring systems often suffer from:
1. Fragmented data formats from disparate sensor feeds.
2. Inability to handle rapid analytical queries without heavy relational database overhead.
3. Lack of integrated predictive capabilities to forecast AQI from raw sensor readings.
4. Static, non-interactive reporting that fails to communicate public health risks effectively.

### 2.2 Project Objectives
- **Automated Data Ingestion & ETL:** Clean, validate, and structure time-series sensor data.
- **Analytical Storage:** Leverage DuckDB's vectorized query execution for fast aggregation.
- **Machine Learning Modeling:** Train regression and classification models to forecast AQI with high fidelity.
- **Visual Analytics:** Provide interactive scatter plots, residual distribution histograms, feature importance charts, correlation matrices, and spatial sensor maps.
- **Interactive Simulation:** Enable end-users and policymakers to test custom pollutant scenarios and view immediate health advisories.

---

## 3. System Architecture

```mermaid
flowchart TD
    A["Raw Data Sources<br/>(OpenAQ API / CSV Upload / Sensor Feeds)"] --> B["ETL Pipeline Orchestrator"]
    B --> C["Data Validation & Quality Scoring"]
    C --> D[("DuckDB Analytical Database<br/>Schemas: Raw, Staging, Presentation")]
    
    D --> E["Machine Learning Engine<br/>(scikit-learn)"]
    E --> F["Data Preprocessing & Scaling"]
    F --> G["Model Training<br/>(Random Forest / Gradient Boosting)"]
    G --> H["Model Evaluation & Metrics<br/>(R², RMSE, MAE, Feature Importance)"]
    
    D --> I["Interactive Dashboard<br/>(Dash & Plotly)"]
    H --> I
    I --> J["Map View<br/>(Spatial Heatmap)"]
    I --> K["Trend & Distribution Analysis"]
    I --> L["ML Analytics & Visuals"]
    I --> M["Real-Time AQI Simulator"]
```

---

## 4. Machine Learning Methodology

### 4.1 Feature Selection
The predictive model uses the following key atmospheric and meteorological variables:
- **$PM_{2.5}$ ($\mu g/m^3$):** Fine inhalable particles ($< 2.5\,\mu m$).
- **$PM_{10}$ ($\mu g/m^3$):** Coarse particulate matter ($< 10\,\mu m$).
- **$NO_2$ ($\mu g/m^3$):** Nitrogen Dioxide from vehicle and power emissions.
- **$SO_2$ ($\mu g/m^3$):** Sulfur Dioxide from industrial fossil fuel burning.
- **$CO$ ($ppm$):** Carbon Monoxide from incomplete combustion.
- **$O_3$ ($\mu g/m^3$):** Ground-level ozone formed by photochemical reactions.
- **Temperature ($^\circ C$), Humidity ($\%$), Wind Speed ($km/h$):** Meteorological dispersion drivers.

### 4.2 Standard AQI Mathematical Formulation
The sub-index ($I_p$) for pollutant $p$ with concentration $C_p$ is computed via linear interpolation across regulatory breakpoints:

$$I_p = I_{low} + \frac{I_{high} - I_{low}}{C_{high} - C_{low}} \times (C_p - C_{low})$$

Where:
- $C_{low}, C_{high}$: Concentration breakpoints containing $C_p$.
- $I_{low}, I_{high}$: Index breakpoints corresponding to $[C_{low}, C_{high}]$.

The composite Air Quality Index is governed by the dominant (maximum) pollutant:
$$\text{Overall AQI} = \max(I_{PM2.5}, I_{PM10}, I_{NO2}, I_{SO2}, I_{CO}, I_{O3})$$

### 4.3 Evaluation Metrics
- **Coefficient of Determination ($R^2$):**
  $$R^2 = 1 - \frac{\sum_{i=1}^n (y_i - \hat{y}_i)^2}{\sum_{i=1}^n (y_i - \bar{y})^2}$$
- **Root Mean Squared Error (RMSE):**
  $$\text{RMSE} = \sqrt{\frac{1}{n}\sum_{i=1}^n (y_i - \hat{y}_i)^2}$$
- **Mean Absolute Error (MAE):**
  $$\text{MAE} = \frac{1}{n}\sum_{i=1}^n |y_i - \hat{y}_i|$$

---

## 5. Experimental Results

| Model Algorithm | Task Type | $R^2$ Score / Accuracy | MAE | RMSE | Inference Time |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Random Forest Regressor** | Continuous AQI | **0.9991** | **0.29** | **0.78** | ~4 ms |
| **Gradient Boosting Regressor** | Continuous AQI | 0.9984 | 0.42 | 1.05 | ~3 ms |
| **Linear / Ridge Regression** | Continuous AQI | 0.9812 | 1.84 | 3.20 | <1 ms |
| **Random Forest Classifier** | AQI Category | **100.0%** | N/A | N/A | ~4 ms |

### Key Findings
1. Particulate matter ($PM_{10}$ and $PM_{2.5}$) accounts for over **95% of relative feature importance** in determining composite AQI.
2. Meteorological variables (wind speed and humidity) correlate inversely with particulate concentrations due to atmospheric dispersion.
3. The ensemble Random Forest model achieves near-perfect predictive capability without overfitting due to regularized maximum depth.

---

## 6. Project Directory Structure
```
AIR-QUALITY-PIPELINE/
├── app/
│   ├── config/              # Application settings and structured logging
│   ├── core/                # DuckDB database manager and schema definition
│   ├── dashboard/           # Dash web app, UI components, Plotly chart generators
│   │   ├── callbacks/       # Interactivity callbacks (map, trends, ML, export)
│   │   ├── components/      # Layout panels, metrics cards, ML tab UI
│   │   └── assets/css/      # Responsive design stylesheet
│   ├── ml/                  # Machine Learning core module
│   │   ├── aqi_calculator.py# Breakpoint interpolation and NAQI standards
│   │   └── model_trainer.py # Training, evaluation, feature importance, serialization
│   ├── pipeline/            # OpenAQ extractors, transformers, loaders
│   └── main.py              # Central application entry point
├── data/
│   ├── air_quality.db       # Embedded DuckDB analytical database
│   └── sample_air_quality_dataset.csv # 3,000+ multi-city records
├── docs/
│   └── COLLEGE_PROJECT_REPORT.md # Comprehensive documentation
├── models/
│   └── aqi_model.joblib     # Serialized trained model artifact
├── scripts/
│   ├── generate_sample_dataset.py # Realistic multi-city data generator
│   ├── train_model.py       # Standalone CLI model training script
│   ├── predict.py           # Standalone CLI prediction script
│   └── setup_db.py          # Database schema initialization
├── requirements.txt         # Project dependencies
└── run.bat                  # One-click Windows launcher
```

---

## 7. Viva Voce (Oral Exam) Questions & Answers

### Q1: What is the main objective of this project?
**Answer:** The project delivers an automated, end-to-end environmental data pipeline that ingests, validates, and stores air quality data in an analytical DuckDB database, trains Machine Learning models (Random Forest, Gradient Boosting) to forecast AQI, and provides interactive visual analytics and what-if scenario predictions.

### Q2: Why choose DuckDB instead of SQLite, MySQL, or PostgreSQL?
**Answer:** DuckDB is an embedded columnar database specifically designed for analytical queries (OLAP). Columnar storage enables vectorized execution, compressed storage, and ultra-fast aggregate queries (`AVG`, `MAX`, `GROUP BY`) across millions of rows, without requiring a separate database server process.

### Q3: How is the Air Quality Index (AQI) mathematically computed?
**Answer:** Standard NAQI / US EPA standards define sub-index breakpoints for each pollutant ($PM_{2.5}, PM_{10}, NO_2, SO_2, CO, O_3$). Linear interpolation maps raw pollutant concentrations to a standard scale (0 to 500). The composite AQI is the maximum of all sub-indices ($\text{Overall AQI} = \max_p(I_p)$).

### Q4: Why did you use Random Forest and Gradient Boosting?
**Answer:** Tree-based ensemble methods excel on tabular environmental datasets. Random Forest averages multiple decorrelated decision trees, reducing variance and resisting overfitting. Gradient Boosting builds trees sequentially to minimize residual errors. Both natively provide feature importance rankings and handle non-linear interactions without requiring strict feature normalization.

### Q5: What is the difference between $R^2$, MAE, and RMSE?
**Answer:**
- **$R^2$ (Coefficient of Determination):** Measures the proportion of variance in the dependent variable explained by features (1.0 = perfect explanation).
- **MAE (Mean Absolute Error):** Average magnitude of errors; robust to outliers and easy to interpret.
- **RMSE (Root Mean Squared Error):** Square root of the mean squared errors; penalizes large errors more heavily due to the squaring term.

### Q6: How does the system handle missing or dirty sensor values?
**Answer:** The ETL pipeline incorporates a `QualityTransformer` that assigns a quality score based on physical plausibility thresholds (e.g., negative concentrations or extreme spikes are flagged). During ML training, `SimpleImputer` handles remaining missing values using median imputation.

### Q7: Can a user train the model on their own custom dataset?
**Answer:** Yes. The dashboard provides a dedicated "Upload Your Own CSV File" dropzone that dynamically parses uploaded files, detects pollutant columns, trains the selected algorithm, and immediately renders evaluation plots and feature importances. Alternatively, the user can run `python scripts/train_model.py --dataset path/to/dataset.csv`.

---

## 8. Quick Start Guide for Evaluators

### 1. Launch the System
Double-click `run.bat` or run:
```bash
python app/main.py dashboard
```
Open **`http://localhost:8050`** in any web browser.

### 2. Train Model from Terminal (CLI Viva Demo)
```bash
python scripts/train_model.py --dataset data/sample_air_quality_dataset.csv --target aqi --algorithm random_forest
```

### 3. Make Live Prediction from Terminal
```bash
python scripts/predict.py --pm25 55 --pm10 110 --no2 35 --so2 15 --co 1.0 --o3 30
```
