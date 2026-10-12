"""
Machine Learning Model Trainer and Predictor for Air Quality Data
Supports both continuous Regression (AQI, PM2.5, PM10) and Category Classification.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
import os
import io
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from app.config.settings import PROJECT_ROOT
from app.config.logging_config import logger
from app.ml.aqi_calculator import enrich_dataframe_with_aqi, calculate_overall_aqi, get_aqi_category_info


MODELS_DIR = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


class AirQualityMLTrainer:
    """Trainer class for Air Quality prediction and evaluation."""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.imputer = None
        self.label_encoder = None
        self.feature_names: List[str] = []
        self.target_name: str = ""
        self.task_type: str = "regression"
        self.algorithm_name: str = ""
        self.metrics: Dict[str, Any] = {}
        self.train_results: Dict[str, Any] = {}
        
    def load_from_csv(self, file_path_or_buffer: Union[str, Path, io.StringIO, io.BytesIO]) -> pd.DataFrame:
        """Load dataset from CSV file or buffer."""
        df = pd.read_csv(file_path_or_buffer)
        df = enrich_dataframe_with_aqi(df)
        return df

    def load_from_database(self) -> pd.DataFrame:
        """Load and pivot data from DuckDB database."""
        from app.core.database import db_manager
        
        query = """
        SELECT 
            location,
            measurement_time,
            parameter,
            value
        FROM raw.measurements
        WHERE quality_score > 0.5
        """
        
        with db_manager.get_connection() as conn:
            raw_df = conn.execute(query).df()
            
        if raw_df.empty:
            raise ValueError("No measurement data available in database.")
            
        # Pivot table to have one column per parameter
        pivoted = raw_df.pivot_table(
            index=["location", "measurement_time"],
            columns="parameter",
            values="value",
            aggfunc="mean"
        ).reset_index()
        
        # Flatten multiindex columns if any
        pivoted.columns = [str(c).lower().replace(".", "").replace("-", "") for c in pivoted.columns]
        
        # Enrich with AQI
        pivoted = enrich_dataframe_with_aqi(pivoted)
        return pivoted

    def prepare_features(
        self,
        df: pd.DataFrame,
        target_column: str,
        task_type: str = "regression",
        feature_columns: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Clean, extract features, and prepare X and y matrices."""
        df_clean = df.copy()
        
        # Normalize column names
        df_clean.columns = [str(c).lower().replace(".", "").replace("-", "").strip() for c in df_clean.columns]
        target_clean = target_column.lower().replace(".", "").replace("-", "").strip()
        
        if target_clean not in df_clean.columns:
            raise ValueError(f"Target column '{target_column}' not found in dataset columns: {list(df_clean.columns)}")

        # Drop rows where target variable is missing
        df_clean = df_clean.dropna(subset=[target_clean]).copy()
            
        # Remove timestamp, categorical, and metadata columns from feature candidates
        exclude_cols = {
            target_clean, "id", "measurement_id", "sensor_id", "location_id", "timestamp", 
            "measurement_time", "ingestion_time", "source", "unit", "dominant_pollutant",
            "city", "station", "stationname", "state", "date", "aqi_bucket", "status", "country"
        }
        
        # Try converting potential numeric columns
        for col in df_clean.columns:
            if col not in exclude_cols:
                converted = pd.to_numeric(df_clean[col], errors='coerce')
                if converted.notna().sum() > 10:  # If at least 10 valid numbers
                    df_clean[col] = converted

        if feature_columns:
            selected_features = [c.lower().replace(".", "").replace("-", "").strip() for c in feature_columns if c.lower() in df_clean.columns and c.lower() != target_clean]
        else:
            # Auto-detect numeric features
            num_cols = df_clean.select_dtypes(include=[np.number]).columns.tolist()
            selected_features = [c for c in num_cols if c not in exclude_cols]
            
        if not selected_features:
            raise ValueError("No valid numeric features found in the dataset to train the model.")
            
        self.df_clean = df_clean
        self.feature_names = selected_features
        self.target_name = target_clean
        self.task_type = task_type
        
        # Separate X and y
        X_df = df_clean[selected_features].copy()
        y_series = df_clean[target_clean].copy()
        
        # Impute missing values for X
        self.imputer = SimpleImputer(strategy="median")
        X = self.imputer.fit_transform(X_df)
        
        # Scale X
        self.scaler = StandardScaler()
        X = self.scaler.fit_transform(X)
        
        if task_type == "classification":
            self.label_encoder = LabelEncoder()
            y = self.label_encoder.fit_transform(y_series.astype(str))
        else:
            y = pd.to_numeric(y_series, errors="coerce").fillna(y_series.median()).values
            
        return X, y, selected_features

    def train(
        self,
        df: pd.DataFrame,
        target_column: str = "aqi",
        algorithm: str = "random_forest",
        task_type: str = "regression",
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """Train and evaluate the ML model."""
        logger.info(f"Training model: target={target_column}, algo={algorithm}, task={task_type}")
        
        # Prepare features
        X, y, features = self.prepare_features(df, target_column, task_type=task_type)
        
        # Train / Test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # Instantiate Model
        if task_type == "regression":
            if algorithm == "random_forest":
                model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=random_state, n_jobs=-1)
            elif algorithm == "gradient_boosting":
                model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=random_state)
            elif algorithm == "linear_regression":
                model = Ridge(alpha=1.0)
            elif algorithm == "decision_tree":
                model = DecisionTreeRegressor(max_depth=8, random_state=random_state)
            else:
                model = RandomForestRegressor(n_estimators=100, random_state=random_state)
        else:
            if algorithm == "random_forest":
                model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=random_state, n_jobs=-1)
            elif algorithm == "gradient_boosting":
                model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=random_state)
            elif algorithm == "logistic_regression":
                model = LogisticRegression(max_iter=1000, random_state=random_state)
            elif algorithm == "decision_tree":
                model = DecisionTreeClassifier(max_depth=8, random_state=random_state)
            else:
                model = RandomForestClassifier(n_estimators=100, random_state=random_state)
                
        # Train
        model.fit(X_train, y_train)
        self.model = model
        self.algorithm_name = algorithm
        
        # Predictions
        y_pred = model.predict(X_test)
        
        # Evaluation Metrics
        metrics = {}
        visual_data = {}
        
        if task_type == "regression":
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Avoid division by zero in MAPE
            denom = np.where(y_test == 0, 1e-6, y_test)
            mape = np.mean(np.abs((y_test - y_pred) / denom)) * 100
            
            metrics = {
                "r2_score": round(float(r2), 4),
                "mae": round(float(mae), 2),
                "rmse": round(float(rmse), 2),
                "mse": round(float(mse), 2),
                "mape": round(float(mape), 2),
                "train_samples": len(X_train),
                "test_samples": len(X_test)
            }
            
            # Actual vs Predicted data
            actual_vs_pred_df = pd.DataFrame({
                "Actual": y_test,
                "Predicted": y_pred,
                "Residual": y_test - y_pred
            })
            
            # Limit points for fast rendering if dataset is massive
            if len(actual_vs_pred_df) > 500:
                actual_vs_pred_df = actual_vs_pred_df.sample(500, random_state=42)
                
            visual_data["actual_vs_pred"] = actual_vs_pred_df.to_dict(orient="records")
            visual_data["residuals"] = (y_test - y_pred).tolist()
            
        else:
            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, average="weighted", zero_division=0)
            rec = recall_score(y_test, y_pred, average="weighted", zero_division=0)
            f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
            cm = confusion_matrix(y_test, y_pred)
            
            classes = self.label_encoder.classes_.tolist()
            metrics = {
                "accuracy": round(float(acc), 4),
                "precision": round(float(prec), 4),
                "recall": round(float(rec), 4),
                "f1_score": round(float(f1), 4),
                "classes": classes,
                "train_samples": len(X_train),
                "test_samples": len(X_test)
            }
            visual_data["confusion_matrix"] = {
                "z": cm.tolist(),
                "x": classes,
                "y": classes
            }
            
        # Feature Importance
        feature_importance_list = []
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
            sorted_idx = np.argsort(importances)[::-1]
            for idx in sorted_idx:
                feature_importance_list.append({
                    "feature": features[idx],
                    "importance": round(float(importances[idx]), 4)
                })
        elif hasattr(model, "coef_"):
            coef = np.abs(model.coef_)
            if coef.ndim > 1:
                coef = coef.mean(axis=0)
            sorted_idx = np.argsort(coef)[::-1]
            for idx in sorted_idx:
                feature_importance_list.append({
                    "feature": features[idx],
                    "importance": round(float(coef[idx]), 4)
                })
                
        visual_data["feature_importance"] = feature_importance_list
        
        # Feature Correlation Matrix (numeric features only)
        clean_df = getattr(self, "df_clean", df)
        corr_cols = [c for c in features if c in clean_df.columns]
        target_norm = target_column.lower().replace(".", "").replace("-", "").strip()
        if target_norm in clean_df.columns and task_type == "regression":
            if target_norm not in corr_cols:
                corr_cols.append(target_norm)
        corr_df = clean_df[corr_cols].select_dtypes(include=[np.number]).corr().fillna(0)
        visual_data["correlation_matrix"] = {
            "z": corr_df.values.round(2).tolist(),
            "x": [str(c).upper() for c in corr_df.columns],
            "y": [str(c).upper() for c in corr_df.columns]
        }
        
        self.metrics = metrics
        self.train_results = {
            "metrics": metrics,
            "visual_data": visual_data,
            "features": features,
            "target": target_column,
            "algorithm": algorithm,
            "task_type": task_type
        }
        
        # Save model automatically
        self.save_model()
        
        return self.train_results

    def save_model(self, file_path: Optional[Union[str, Path]] = None) -> str:
        """Save trained model and preprocessing pipeline to disk."""
        if self.model is None:
            raise ValueError("No model trained yet to save.")
            
        path = Path(file_path) if file_path else MODELS_DIR / "aqi_model.joblib"
        bundle = {
            "model": self.model,
            "scaler": self.scaler,
            "imputer": self.imputer,
            "label_encoder": self.label_encoder,
            "feature_names": self.feature_names,
            "target_name": self.target_name,
            "task_type": self.task_type,
            "algorithm_name": self.algorithm_name,
            "metrics": self.metrics
        }
        joblib.dump(bundle, path)
        logger.info(f"Model saved successfully to {path}")
        return str(path)

    def load_model(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        """Load model bundle from disk."""
        path = Path(file_path) if file_path else MODELS_DIR / "aqi_model.joblib"
        if not path.exists():
            return False
            
        bundle = joblib.load(path)
        self.model = bundle["model"]
        self.scaler = bundle["scaler"]
        self.imputer = bundle["imputer"]
        self.label_encoder = bundle["label_encoder"]
        self.feature_names = bundle["feature_names"]
        self.target_name = bundle["target_name"]
        self.task_type = bundle["task_type"]
        self.algorithm_name = bundle.get("algorithm_name", "model")
        self.metrics = bundle.get("metrics", {})
        return True

    def predict_single(self, input_data: Dict[str, float]) -> Dict[str, Any]:
        """Make a prediction on a single record of features."""
        if self.model is None:
            # Try to load existing model
            if not self.load_model():
                raise ValueError("No model trained or available. Please train a model first.")
                
        # Build feature vector
        row = []
        for feat in self.feature_names:
            feat_lower = feat.lower()
            val = input_data.get(feat_lower, input_data.get(feat, np.nan))
            row.append(val)
            
        X_df = pd.DataFrame([row], columns=self.feature_names)
        X_imp = self.imputer.transform(X_df)
        X_scaled = self.scaler.transform(X_imp)
        
        pred = self.model.predict(X_scaled)[0]
        
        if self.task_type == "classification":
            category = self.label_encoder.inverse_transform([pred])[0]
            cat_info = {"category": category, "color": "#3b82f6", "advice": "Predicted Category"}
            for low, high, c_name, c_col, c_adv in [
                (0, 50, "Good", "#10b981", "Clean air quality."),
                (51, 100, "Satisfactory", "#3b82f6", "Acceptable air."),
                (101, 200, "Moderate", "#f59e0b", "Noticeable pollution."),
                (201, 300, "Poor", "#f97316", "Unhealthy air."),
                (301, 400, "Very Poor", "#ef4444", "Hazardous pollution."),
                (401, 9999, "Severe", "#7f1d1d", "Emergency toxicity.")
            ]:
                if c_name.lower() == str(category).lower():
                    cat_info = {"category": c_name, "color": c_col, "advice": c_adv}
                    break
                    
            return {
                "prediction": category,
                "predicted_value": category,
                "category": cat_info["category"],
                "color": cat_info["color"],
                "advice": cat_info["advice"],
                "task_type": "classification"
            }
        else:
            predicted_val = round(float(pred), 2)
            cat_info = get_aqi_category_info(predicted_val)
            return {
                "prediction": predicted_val,
                "predicted_value": predicted_val,
                "category": cat_info["category"],
                "color": cat_info["color"],
                "advice": cat_info["advice"],
                "task_type": "regression"
            }


# Global instance
ml_trainer = AirQualityMLTrainer()
