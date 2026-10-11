"""
Command-Line Machine Learning Model Training Script
Allows college students and evaluators to train models directly on any air quality dataset.

Usage:
    python scripts/train_model.py --dataset data/sample_air_quality_dataset.csv --target aqi --algorithm random_forest
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ml.model_trainer import ml_trainer
from app.config.settings import PROJECT_ROOT


def main():
    parser = argparse.ArgumentParser(
        description="Air Quality Machine Learning Model Trainer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/train_model.py --dataset data/sample_air_quality_dataset.csv --target aqi --algorithm random_forest
  python scripts/train_model.py --dataset data/sample_air_quality_dataset.csv --target aqi_category --algorithm random_forest
  python scripts/train_model.py --source database --target aqi --algorithm gradient_boosting
        """
    )
    
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/sample_air_quality_dataset.csv",
        help="Path to CSV dataset file (default: data/sample_air_quality_dataset.csv)"
    )
    parser.add_argument(
        "--source",
        choices=["csv", "database"],
        default="csv",
        help="Source of training data ('csv' or 'database')"
    )
    parser.add_argument(
        "--target",
        type=str,
        default="aqi",
        help="Target column to predict (e.g., 'aqi', 'pm25', 'pm10', 'aqi_category')"
    )
    parser.add_argument(
        "--algorithm",
        choices=["random_forest", "gradient_boosting", "linear_regression", "decision_tree"],
        default="random_forest",
        help="Machine learning algorithm to train"
    )
    parser.add_argument(
        "--test-split",
        type=float,
        default=0.2,
        help="Test split fraction (default: 0.2)"
    )
    
    args = parser.parse_args()
    
    print("=" * 65)
    print("      AIR QUALITY PIPELINE - MACHINE LEARNING TRAINER")
    print("=" * 65)
    
    # Load dataset
    if args.source == "database":
        print("[*] Loading measurements from DuckDB database...")
        df = ml_trainer.load_from_database()
    else:
        dataset_path = Path(args.dataset)
        if not dataset_path.exists():
            print(f"[*] Dataset not found at {dataset_path}. Generating realistic multi-city sample dataset...")
            from scripts.generate_sample_dataset import generate_dataset
            df = generate_dataset(output_path=str(dataset_path))
        else:
            print(f"[*] Loading dataset from: {dataset_path}")
            df = ml_trainer.load_from_csv(dataset_path)
            
    print(f"[+] Loaded {len(df):,} total records with columns: {list(df.columns)}")
    
    task_type = "classification" if args.target.lower() == "aqi_category" else "regression"
    print(f"[*] Task Type: {task_type.upper()}")
    print(f"[*] Target Column: {args.target}")
    print(f"[*] Algorithm: {args.algorithm.replace('_', ' ').title()}")
    print(f"[*] Test Ratio: {args.test_split * 100:.0f}%")
    print("\n[*] Training model now...")
    
    results = ml_trainer.train(
        df=df,
        target_column=args.target,
        algorithm=args.algorithm,
        task_type=task_type,
        test_size=args.test_split
    )
    
    metrics = results["metrics"]
    print("\n" + "=" * 65)
    print("              MODEL EVALUATION RESULTS")
    print("=" * 65)
    
    if task_type == "regression":
        print(f"  R^2 Score (Variance Explained):  {metrics['r2_score']:.4f} (Ideal: 1.0000)")
        print(f"  Mean Absolute Error (MAE):       {metrics['mae']:.2f}")
        print(f"  Root Mean Squared Error (RMSE):  {metrics['rmse']:.2f}")
        print(f"  Mean Squared Error (MSE):        {metrics['mse']:.2f}")
        print(f"  Mean Abs Percentage Error (MAPE):{metrics['mape']:.2f}%")
    else:
        print(f"  Accuracy Score:                  {metrics['accuracy'] * 100:.2f}%")
        print(f"  Precision (Weighted):            {metrics['precision']:.4f}")
        print(f"  Recall (Weighted):               {metrics['recall']:.4f}")
        print(f"  F1-Score (Weighted):             {metrics['f1_score']:.4f}")
        print(f"  Detected Classes:                {', '.join(metrics['classes'])}")
        
    print(f"  Training Samples:                {metrics['train_samples']:,}")
    print(f"  Testing Samples:                 {metrics['test_samples']:,}")
    
    print("\n--- TOP FEATURE IMPORTANCE ---")
    feat_imp = results["visual_data"].get("feature_importance", [])
    for idx, item in enumerate(feat_imp[:6], 1):
        print(f"  {idx}. {item['feature'].upper():<14} : {item['importance']:.4f}")
        
    save_path = PROJECT_ROOT / "models" / "aqi_model.joblib"
    print(f"\n[+] Saved model artifact to: {save_path}")
    print("=" * 65)
    print("[OK] Model training completed successfully!")


if __name__ == "__main__":
    main()
