# Deploying the Air Quality Intelligence Platform on Render (Free Cloud Hosting)

This guide provides step-by-step instructions for deploying your **Air Quality Monitoring & AI/ML Analytics System** live on **[Render.com](https://render.com)** so you can share a live public URL with your professor and college examiners.

---

## 1. Quick Architecture Overview

Your repository includes everything required for production cloud deployment:
- **[`wsgi.py`](../wsgi.py)**: Exposes the underlying Flask WSGI application instance.
- **[`Procfile`](../Procfile)**: Declares the web service process for Gunicorn.
- **[`render.yaml`](../render.yaml)**: Blueprint specifying environment, build, and start commands.
- **[`requirements.txt`](../requirements.txt)**: Optimized production Python dependencies.

---

## 2. Step-by-Step Render Deployment Guide (2 Minutes)

### Step 1: Push your Code to GitHub
Ensure all latest files are on your GitHub repository:
```bash
git push origin main
```
Repository URL: `https://github.com/Devendra2306/AIR-QUALITY`

### Step 2: Sign Up / Log In to Render
1. Visit [render.com](https://render.com).
2. Click **Get Started** or **Log In** with your **GitHub Account**.

### Step 3: Create a New Web Service
1. In your Render Dashboard, click the blue **New +** button in the top right.
2. Select **Web Service**.
3. Choose **Build and deploy from a Git repository** and click **Next**.
4. Select your repository: `Devendra2306/AIR-QUALITY` (if not visible, click *Configure account* to grant access).

### Step 4: Configure Service Settings
Fill in the following standard fields:
- **Name**: `air-quality-analytics` (or any custom name)
- **Region**: `Singapore` or `Frankfurt` (closest to India)
- **Branch**: `main`
- **Root Directory**: *(leave blank)*
- **Runtime**: `Python 3`
- **Build Command**:
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command**:
  ```bash
  gunicorn wsgi:server --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT
  ```
- **Instance Type**: Select **Free** ($0 / month).

### Step 5: Click "Create Web Service"
- Render will start building the project automatically.
- Within 2-3 minutes, you will see `Build successful` and `Service live`.
- Your public URL will look like:
  ```text
  https://air-quality-analytics.onrender.com
  ```

---

## 3. College Presentation Flow (Colab + Live Website)

When presenting to your professor:

### Step 1: Open the Live Web Platform
- Open your live Render link (or `http://localhost:8050` if running locally).
- Click on **"AI/ML Lab Insights (Exp 1-10)"** tab:
  1. **A* Search Corridor**: Select **Delhi** as Origin and **Bengaluru** as Destination $\rightarrow$ Click *Compute Optimal A* Route*. Show how the algorithm dynamically routes travel through clean-air waypoints (Bhopal, Nagpur, Hyderabad).
  2. **Hypothesis Testing**: Show the T-test card proving metropolitan pollution is statistically significantly higher than regional towns ($p < 0.05$).
  3. **K-Means Clustering**: Show how the 419 stations are partitioned into 3 severity tiers, and point to the Elbow curve.
  4. **PCA Dimensionality Reduction**: Show the 2D compression of 7 criteria pollutants.
  5. **Model Leaderboard**: Walk through the comparison table showing why Random Forest achieved $R^2 = 0.996$.

### Step 2: Open the Google Colab Notebook
- Open [Google Colab](https://colab.research.google.com).
- Upload `Air_Quality_AI_ML_Mini_Project_Colab.ipynb`.
- Walk through Experiments 1 to 10 step-by-step to show the theory, equations, data cleaning, and algorithmic code.
