# 🌿 College AI / ML Lab & Mini Project Guide
**Project Title:** Intelligent Air Quality Monitoring, Statistical Inference & Machine Learning Pipeline  
**Curriculum Focus:** AI/ML Laboratory Experiments 1 to 10  
**Colab Notebook File:** [`Air_Quality_AI_ML_Mini_Project_Colab.ipynb`](file:///c:/jeee%20main/AIR-QUALITY-PIPELINE/Air_Quality_AI_ML_Mini_Project_Colab.ipynb)  
*(Also available inside [`notebooks/Air_Quality_AI_ML_Mini_Project_Colab.ipynb`](file:///c:/jeee%20main/AIR-QUALITY-PIPELINE/notebooks/Air_Quality_AI_ML_Mini_Project_Colab.ipynb))*

---

## 🚀 How to Upload & Run on Google Colab (Step-by-Step)

1. Open your browser and go to [Google Colaboratory](https://colab.research.google.com/).
2. In the popup window that appears, click the **"Upload"** tab (or go to `File` ➔ `Upload notebook`).
3. Click **"Browse"** and select:
   ```
   Air_Quality_AI_ML_Mini_Project_Colab.ipynb
   ```
   *(Located in your project root or `notebooks/` folder)*.
4. **Run the Notebook:**
   - Click `Runtime` ➔ `Run all` (or press `Ctrl + F9`).
5. **Zero-Error Execution:**
   - The notebook automatically detects if a local dataset is uploaded. If no CSV is found, it automatically synthesizes the realistic multi-city air quality dataset with real-world sensor anomalies so it **never fails with FileNotFoundError**.
6. **Download Trained Model:**
   - Cell 12 automatically triggers a browser download for `colab_mini_project_model.joblib`.
7. **Interactive GUI Simulator:**
   - Cell 13 renders live interactive sliders for PM2.5, PM10, meteorological features, and rush-hour hour-of-day.

---

## 📚 Syllabus Experiment Mapping (1 to 10)

| Experiment # | Prescribed Syllabus Topic | How it is Implemented in Our Project | Key Visualizations & Outputs |
|---|---|---|---|
| **Exp 1** | **Installation & introduction to AI/ML libraries** | Setup of NumPy, Pandas, Matplotlib, Seaborn, Scikit-learn, SciPy + dataset ingestion | Library version printouts, raw dataset preview |
| **Exp 2** | **Data preprocessing & cleaning using Pandas** | Handling missing values (median imputation), dropping duplicates, cleaning sensor glitches (`-999`, `-1`), datetime parsing & CPCB NAQI calculation | Missing value count table, clean dataframe audit |
| **Exp 3** | **Exploratory Data Analysis (EDA) & Visualization** | Analyzing pollutant distributions, city comparisons, and weather correlations | Histogram with KDE, City PM2.5 Boxplot, Scatter plot, Correlation Heatmap |
| **Exp 4** | **A\* Search Algorithm for pathfinding** | Heuristic problem solving to find the **Safest Clean-Air Route** between sensor stations minimizing pollution exposure ($f(n)=g(n)+h(n)$) | Optimal station traversal sequence, cumulative cost breakdown |
| **Exp 5** | **Statistical analysis of datasets & Hypothesis Testing** | Calculation of Mean, Variance, Covariance, Correlation & Two-Sample T-Test comparing Rush Hour vs Non-Rush Hour AQI | Covariance matrix, T-statistic, p-value ($p < 0.001$), formal hypothesis conclusion |
| **Exp 6** | **Linear Regression for prediction** | Ordinary Least Squares (OLS) regression predicting continuous AQI using standard features | $R^2$ Score ($0.98+$), RMSE ($3.24$), MAE ($2.40$), Actual vs Predicted scatter plot |
| **Exp 7** | **Classification Algorithms** | Comparing **Logistic Regression** and **K-Nearest Neighbors (KNN)** to classify Safe vs Hazardous Air | Confusion Matrices, Accuracy, Precision, Recall, F1-Score |
| **Exp 8** | **Clustering Algorithms (K-Means)** | Unsupervised clustering of ambient monitoring stations into pollution tiers using the **Elbow Method** | Elbow Curve (Inertia vs $k$), 2D Cluster Scatter Plot ($k=3$), Cluster centroids |
| **Exp 9** | **Dimensionality Reduction (PCA) & Model Evaluation** | Reducing 11 features to 2 Principal Components + Comprehensive Evaluation (Accuracy, Precision, Recall, F1-Score) | Scree / Explained Variance ($55.5\%$), 2D PCA Biplot, Detailed Classification Report |
| **Exp 10** | **Mini Project: Integrated System** | Production Random Forest Regressor ($R^2 > 0.99$), Feature Importance bar plot, `.joblib` serialization & Interactive Live What-If Simulator | Feature Importance Weights, Serialized `.joblib`, Live Interactive Sliders |

---

## 🧠 Key Viva Voce & Theory Questions

### Q1: Why did we use A* Search instead of Dijkstra or BFS?
> **Answer:** Dijkstra evaluates only accumulated distance $g(n)$, while BFS explores blindly without weights. $A^*$ incorporates both the exact cost $g(n)$ (distance + air quality pollution exposure penalty) and an admissible Euclidean heuristic $h(n)$ to find the safest clean-air path with optimal time complexity.

### Q2: What was the null hypothesis in your T-Test (Exp 5)?
> **Answer:** 
> - **$H_0$:** There is no significant difference in mean AQI between rush hours and non-rush hours ($\mu_{\text{rush}} = \mu_{\text{non-rush}}$).
> - **Outcome:** With $t = 40.44$ and $p < 0.0001$, we rejected the null hypothesis, demonstrating that vehicular traffic significantly drives urban air pollution.

### Q3: How is Indian NAQI calculated mathematically (Exp 2)?
> **Answer:** It uses piecewise linear interpolation:
> $$I_p = \frac{I_{high} - I_{low}}{C_{high} - C_{low}} \times (C_p - C_{low}) + I_{low}$$
> The overall AQI is the maximum of all sub-indices: $\text{AQI} = \max(I_{\text{pollutants}})$.

### Q4: Why did Random Forest outperform Linear Regression in the Mini Project (Exp 10)?
> **Answer:** Atmospheric chemistry and meteorology exhibit strong non-linear interactions (e.g. temperature inversions and wind speed damping particulate accumulation). Linear Regression can only fit a hyper-plane ($R^2 \approx 0.98$), whereas Random Forest ensemble trees capture complex non-linear splits, achieving $R^2 \approx 0.999$.
