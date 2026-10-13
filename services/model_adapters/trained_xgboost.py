
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from services.model_adapters.contracts import InferenceResult, ModelStatus


class TrainedXGBoostAMLAdapter:
    """Adapter for the trained transaction-level IBM AML XGBoost model."""

    def __init__(self) -> None:
        root = Path(__file__).resolve().parents[2]
        self.model_path = root / "artifacts" / "aml_xgboost" / "xgboost_aml.joblib"
        self.schema_path = root / "artifacts" / "aml_xgboost" / "feature_schema.json"
        self._model = None
        self._schema = None

    def _load(self) -> None:
        import json

        if self._model is None:
            if not self.model_path.is_file():
                raise FileNotFoundError(f"Model artifact not found: {self.model_path}")
            if not self.schema_path.is_file():
                raise FileNotFoundError(f"Feature schema not found: {self.schema_path}")

            self._model = joblib.load(self.model_path)
            with self.schema_path.open("r", encoding="utf-8") as f:
                self._schema = json.load(f)

    def predict_transaction(self, row: dict[str, Any]) -> InferenceResult[dict[str, Any]]:
        try:
            self._load()
            assert self._schema is not None
            assert self._model is not None

            received = max(0.0, float(row["Amount Received"]))
            paid = max(0.0, float(row["Amount Paid"]))

            timestamp = pd.to_datetime(row["Timestamp"], errors="raise")
            features = {
                "log_received": np.log1p(received),
                "log_paid": np.log1p(paid),
                "log_amount_difference": np.log1p(received) - np.log1p(paid),
                "currency_mismatch": int(
                    str(row["Receiving Currency"]) != str(row["Payment Currency"])
                ),
                "same_account": int(str(row["Account"]) == str(row["Account.1"])),
                "same_bank": int(str(row["From Bank"]) == str(row["To Bank"])),
                "hour": timestamp.hour,
                "minute": timestamp.minute,
                "day_of_week": timestamp.dayofweek,
                "day_of_month": timestamp.day,
            }

            categorical_columns = [
                "From Bank",
                "To Bank",
                "Receiving Currency",
                "Payment Currency",
                "Payment Format",
            ]
            for column in categorical_columns:
                value = str(row[column])
                allowed = self._schema["category_values"][column]
                if value not in allowed:
                    value = "__UNKNOWN__"
                features[column] = value

            feature_order = self._schema["feature_columns"]
            X = pd.DataFrame([features], columns=feature_order)

            for column in categorical_columns:
                X[column] = pd.Categorical(
                    X[column],
                    categories=self._schema["category_values"][column],
                )

            score = float(self._model.predict_proba(X)[0][1])

            return InferenceResult(
                model_name="xgboost_aml",
                status=ModelStatus.AVAILABLE,
                score=score,
                model_version="ibm-aml-xgboost-v1",
                output={
                    "ranking_score": score,
                    "feature_count": len(feature_order),
                    "interpretation": (
                        "Experimental transaction-level AML ranking score; "
                        "not a calibrated probability or a confirmed fraud finding."
                    ),
                },
            )

        except FileNotFoundError as exc:
            return InferenceResult(
                model_name="xgboost_aml",
                status=ModelStatus.UNAVAILABLE,
                error=str(exc),
            )
        except Exception as exc:
            return InferenceResult(
                model_name="xgboost_aml",
                status=ModelStatus.ERROR,
                error=f"{type(exc).__name__}: {exc}",
            )
