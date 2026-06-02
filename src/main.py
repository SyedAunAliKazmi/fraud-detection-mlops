from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from contextlib import asynccontextmanager
from typing import List
import joblib
import numpy as np
import os
from prometheus_fastapi_instrumentator import Instrumentator

MODEL_PATH = os.getenv("MODEL_PATH", "models/fraud_model.pkl")
model = None

# ── Lifespan (replaces deprecated @app.on_event) ──────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"Model not found at {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)
    print(f"✓ Model loaded from {MODEL_PATH}")
    yield

# ── App init ──────────────────────────────────────────────────
app = FastAPI(
    title="Real-Time Fraud Detection API",
    description="MLOps Project 4 — Syed Aun Ali Kazmi (SAP: 70149156)",
    version="1.0.0",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)

# ── Request schema ────────────────────────────────────────────
class Transaction(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"features": [
        0.0, -1.36, -0.07, 2.54, 1.38, -0.34, 0.46, 0.24,
        0.10, 0.36, 0.09, -0.55, -0.62, -0.99, -0.31, 1.47,
        -0.47, 0.21, 0.02, 0.40, 0.25, -0.02, 0.28, -0.11,
        0.07, 0.13, -0.19, 0.13, -0.02, 149.62
    ]}})

    features: List[float] = Field(
        ..., min_length=30, max_length=30,
        description="30 values: [Time, V1-V28, Amount]"
    )

# ── Endpoints ─────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "project":  "Real-Time Fraud Detection System",
        "author":   "Syed Aun Ali Kazmi",
        "sap_id":   "70149156",
        "version":  "1.0.0",
        "docs":     "/docs",
        "metrics":  "/metrics",
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": model is not None}

@app.post("/predict")
def predict(transaction: Transaction):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    X = np.array(transaction.features).reshape(1, -1)
    prediction = int(model.predict(X)[0])
    probability = float(model.predict_proba(X)[0][1])
    return {
        "prediction":        prediction,
        "label":             "FRAUD" if prediction == 1 else "LEGITIMATE",
        "fraud_probability": round(probability, 4),
        "confidence":        round(max(probability, 1 - probability), 4),
    }
