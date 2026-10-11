@echo off
title Air Quality Monitoring & ML Analytics System
color 0A

echo =====================================================================
echo          AIR QUALITY MONITORING & MACHINE LEARNING PIPELINE
echo                    College Minor Project Edition
echo =====================================================================
echo.

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [!] Virtual environment not found in .\venv. Using system Python.
)

echo [1] Launch Interactive Web Dashboard (Map + Trends + ML Visuals)
echo [2] Launch Jupyter Notebook (Data Cleaning, Preprocessing & ML Training)
echo [3] Train Machine Learning Model (CLI)
echo [4] Run Real-Time AQI Predictor (CLI)
echo [5] Regenerate Raw/Sample Datasets & Seed Database
echo [6] Exit
echo.

set /p choice="Select an option [default is 1]: "

if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo.
    echo [*] Starting Air Quality Web Dashboard...
    echo [*] Access in browser at: http://localhost:8050
    python app/main.py dashboard
) else if "%choice%"=="2" (
    echo.
    echo [*] Launching Jupyter Notebook for College Project...
    echo [*] Opening notebooks\Air_Quality_ML_Pipeline_and_Model_Training.ipynb...
    jupyter notebook notebooks\Air_Quality_ML_Pipeline_and_Model_Training.ipynb
) else if "%choice%"=="3" (
    echo.
    echo [*] Training Machine Learning Models...
    python scripts/train_model.py --dataset data/sample_air_quality_dataset.csv --target aqi --algorithm random_forest
    pause
) else if "%choice%"=="4" (
    echo.
    echo [*] Running Air Quality Predictor...
    python scripts/predict.py
    pause
) else if "%choice%"=="5" (
    echo.
    echo [*] Generating datasets and seeding DuckDB...
    python scripts/generate_raw_data.py
    python scripts/generate_sample_dataset.py
    pause
) else (
    echo Exiting...
)
