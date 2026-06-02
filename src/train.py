import pandas as pd
import numpy as np
import joblib
import mlflow
import mlflow.sklearn
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report
)

# ── MLflow setup ──────────────────────────────────────────────
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "file:./mlruns")
mlflow.set_tracking_uri(MLFLOW_URI)
mlflow.set_experiment("fraud-detection-rf")


def train():
    # ── Load real dataset ─────────────────────────────────────
    data_path = os.getenv("DATA_PATH", "data/creditcard.csv")
    print(f"Loading dataset from {data_path} ...")
    df = pd.read_csv(data_path)

    print(f"Dataset: {df.shape[0]:,} rows | {df['Class'].sum()} fraud | {df['Class'].mean()*100:.3f}% fraud rate")

    # ── Features & target ─────────────────────────────────────
    X = df.drop("Class", axis=1).values   # shape: (284807, 30)
    y = df["Class"].values

    # ── Train/test split (stratified) ─────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # ── Pipeline: scale Time (col 0) and Amount (col 29) ──────
    preprocessor = ColumnTransformer([
        ("scaler", StandardScaler(), [0, 29])
    ], remainder="passthrough")

    # ── Model parameters ──────────────────────────────────────
    params = {
        "n_estimators": 100,
        "max_depth": 10,
        "class_weight": "balanced",
        "random_state": 42,
        "n_jobs": -1,
    }

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(**params)),
    ])

    # ── Train & log with MLflow ───────────────────────────────
    with mlflow.start_run(run_name="RandomForest-FraudDetection"):
        print("Training Random Forest ...")
        pipeline.fit(X_train, y_train)

        y_pred = pipeline.predict(X_test)
        y_prob = pipeline.predict_proba(X_test)[:, 1]

        metrics = {
            "accuracy":  accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred),
            "recall":    recall_score(y_test, y_pred),
            "f1_score":  f1_score(y_test, y_pred),
            "roc_auc":   roc_auc_score(y_test, y_prob),
        }

        print("\n=== Model Metrics ===")
        for k, v in metrics.items():
            print(f"  {k}: {v:.4f}")
        print(classification_report(y_test, y_pred,
              target_names=["Legitimate", "Fraud"]))

        # Log everything to MLflow
        mlflow.log_params(params)
        mlflow.log_params({
            "dataset_rows": len(df),
            "fraud_cases":  int(df["Class"].sum()),
            "test_size":    0.2,
            "author":       "Syed Aun Ali Kazmi",
            "sap_id":       "70149156",
        })
        mlflow.log_metrics(metrics)

        # Save model as pickle (used by Docker)
        os.makedirs("models", exist_ok=True)
        joblib.dump(pipeline, "models/fraud_model.pkl")
        print("Model saved → models/fraud_model.pkl")

        # Log & register model in MLflow Model Registry
        mlflow.sklearn.log_model(
            pipeline,
            "fraud-detection-model",
            registered_model_name="FraudDetectionModel",
        )
        run_id = mlflow.active_run().info.run_id
        print(f"Run ID: {run_id}")
        print("Model registered in MLflow Model Registry ✓")


if __name__ == "__main__":
    train()
