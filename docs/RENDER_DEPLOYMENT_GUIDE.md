# 🚀 Step-by-Step Render Deployment Guide

This guide walks you through deploying the **Air Quality Monitoring & Machine Learning Pipeline** to [Render](https://render.com) so anyone, including your college professors and evaluators, can access your live project from anywhere on the internet.

---

## 📋 Overview of Deployment Settings

| Setting | Value |
| :--- | :--- |
| **Service Type** | Web Service |
| **Language / Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt && python scripts/generate_sample_dataset.py` |
| **Start Command** | `gunicorn app.dashboard.app:server --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120` |
| **Instance Type** | Free |
| **Python Version** | `3.11.8` |

---

## 🪜 Step-by-Step Instructions

### Step 1: Push Code to GitHub

Open your terminal in the project directory and push all latest changes to your GitHub repository:

```bash
git add .
git commit -m "Configure project for Render deployment with ML models"
git push origin main
```

*(If you haven't connected a GitHub repository yet, create a new repository on [github.com](https://github.com), copy the repository URL, and run `git remote add origin <your-repo-url>` followed by `git push -u origin main`).*

---

### Step 2: Sign Up on Render

1. Go to **[https://render.com](https://render.com)**.
2. Click **"Get Started"** or **"Sign In"**.
3. Sign in with your **GitHub account** (this makes connecting repositories instant).

---

### Step 3: Create a New Web Service

1. On the Render Dashboard, click the blue **"New +"** button in the top right.
2. Select **"Web Service"**.
3. Under **"Connect a repository"**, select your repository: `AIR-QUALITY-PIPELINE` (or search for its name).
4. Click **"Connect"**.

---

### Step 4: Configure Web Service Parameters

Fill in the configuration fields on the creation screen:

1. **Name:** `air-quality-pipeline` *(or any custom name like `my-college-aqi-project`)*.
2. **Region:** Choose the region closest to you (e.g. `Singapore` or `Oregon`).
3. **Branch:** `main` *(or `master`)*.
4. **Root Directory:** Leave blank *(defaults to root)*.
5. **Runtime:** Select **`Python 3`**.
6. **Build Command:**
   ```bash
   pip install -r requirements.txt && python scripts/generate_sample_dataset.py
   ```
   *(This installs all packages, creates the sample dataset, and initializes DuckDB tables).*
7. **Start Command:**
   ```bash
   gunicorn app.dashboard.app:server --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120
   ```
8. **Instance Type:** Select **`Free`** ($0 / month).

---

### Step 5: Add Environment Variables

Scroll down to the **"Environment Variables"** section and click **"Add Environment Variable"**:

| Key | Value | Purpose |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.11.8` | Specifies stable Python version |
| `ENVIRONMENT` | `production` | Enables production settings |
| `DEBUG` | `false` | Disables debug mode in production |
| `DATABASE_PATH` | `data/air_quality.db` | Embedded DuckDB path |
| `SECRET_KEY` | *(Click "Generate" or type a secret key)* | Security token encryption |

---

### Step 6: Deploy the Web Service

1. Click **"Create Web Service"** at the bottom of the page.
2. Render will start the build process:
   - Pulling code from GitHub
   - Installing Python dependencies from `requirements.txt`
   - Generating 3,000+ air quality records and seeding DuckDB
   - Launching Gunicorn WSGI server
3. You will see live build logs in the console. When it says:
   ```
   ==> Starting service with 'gunicorn app.dashboard.app:server ...'
   [INFO] Listening at: http://0.0.0.0:10000
   ==> Your service is live 🎉
   ```
4. Click the public URL at the top left of the page (e.g., `https://air-quality-pipeline-xxxx.onrender.com`).
5. Your interactive dashboard is now live on the internet!

---

## 💡 Important Tips for Evaluator Demos

1. **Cold Start Wake-up Time:**  
   On Render's Free tier, if the web app receives no visits for 15 minutes, it goes into a temporary sleep mode to conserve resources. When you open the URL again, it takes **40 to 60 seconds** to wake up.  
   > **Viva Tip:** Open your Render link 2 minutes before your professor/examiner evaluates your project so the site is already awake and loads instantly!
2. **Self-Healing Database:**  
   The application code automatically checks if `data/air_quality.db` exists. If Render ever spins down or resets the container, the app auto-seeds fresh records and trains the default ML model upon restart.
3. **Sharing with Professors:**  
   You can submit your live `.onrender.com` link in your project report and presentation slides so evaluators can test the map, trends, and ML prediction simulator on their own phones or laptops.
