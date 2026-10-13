import json
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts" / "aml_xgboost"

model_path = ARTIFACT_DIR / "xgboost_aml.joblib"
schema_path = ARTIFACT_DIR / "feature_schema.json"
report_path = ARTIFACT_DIR / "evaluation_report.json"

for path in (model_path, schema_path, report_path):
    if not path.is_file():
        raise FileNotFoundError(f"Missing artifact: {path}")

model = joblib.load(model_path)

with schema_path.open("r", encoding="utf-8") as f:
    schema = json.load(f)

with report_path.open("r", encoding="utf-8") as f:
    report = json.load(f)

print("Model loaded:", type(model).__name__)
print("Expected features:", len(schema["feature_columns"]))
print("Feature names:", schema["feature_columns"])
print("Validation ROC-AUC:", report["evaluation"]["validation"]["roc_auc"])
print("Test ROC-AUC:", report["evaluation"]["test"]["roc_auc"])

assert model.n_features_in_ == len(schema["feature_columns"]), (
    "Model feature count doesn't match feature schema."
)

print("Artifact verification passed.")