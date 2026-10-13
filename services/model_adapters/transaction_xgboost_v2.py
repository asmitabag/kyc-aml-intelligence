from pathlib import Path
from typing import Any
import json

import joblib
import pandas as pd

from services.model_adapters.contracts import InferenceResult, ModelStatus


class TransactionXGBoostV2Adapter:
    """Adapter for the experimental synthetic-data transaction AML model."""

    MODEL_NAME = "xgboost_aml_v2"
    MODEL_VERSION = "2.1.0"

    def __init__(self) -> None:
        root = Path(__file__).resolve().parents[2]
        artifact_dir = root / "artifacts" / "aml_xgboost_v2"
        self.model_path = artifact_dir / "transaction_xgboost_pipeline.joblib"
        self.schema_path = artifact_dir / "feature_schema.json"
        self._model = None
        self._schema = None

    def _load(self) -> None:
        if self._model is not None:
            return

        if not self.model_path.is_file():
            raise FileNotFoundError(
                f"Model artifact not found: {self.model_path}"
            )
        if not self.schema_path.is_file():
            raise FileNotFoundError(
                f"Feature schema not found: {self.schema_path}"
            )

        with self.schema_path.open("r", encoding="utf-8-sig") as file:
            schema = json.load(file)

        model = joblib.load(self.model_path)

        self._schema = schema
        self._model = model

    def predict_transaction(
        self, row: dict[str, Any]
    ) -> InferenceResult[dict[str, Any]]:
        try:
            self._load()
            assert self._model is not None
            assert self._schema is not None

            timestamp = pd.to_datetime(
                row["Timestamp"], errors="raise", utc=True
            )
            received = float(row["Amount Received"])
            paid = float(row["Amount Paid"])

            if received < 0 or paid < 0:
                raise ValueError("Transaction amounts cannot be negative")

            features = {
                "hour": timestamp.hour,
                "day_of_week": timestamp.dayofweek,
                "day_of_month": timestamp.day,
                "month": timestamp.month,
                "Amount Received": received,
                "Amount Paid": paid,
                "amount_difference": received - paid,
                "total_amount": received + paid,
                "currency_mismatch": int(
                    str(row["Receiving Currency"])
                    != str(row["Payment Currency"])
                ),
                "Receiving Currency": str(row["Receiving Currency"]),
                "Payment Currency": str(row["Payment Currency"]),
                "Payment Format": str(row["Payment Format"]),
                "same_account": int(
                    str(row["Account"]) == str(row["Account.1"])
                ),
                "same_bank": int(
                    str(row["From Bank"]) == str(row["To Bank"])
                ),
            }

            feature_order = self._schema["model_features"]
            X = pd.DataFrame([features], columns=feature_order)

            # Preprocessing is already included in the fitted pipeline.
            score = float(self._model.predict_proba(X)[0, 1])

            return InferenceResult(
                model_name=self.MODEL_NAME,
                status=ModelStatus.AVAILABLE,
                score=score,
                model_version=self.MODEL_VERSION,
                output={
                    "ranking_score": score,
                    "feature_count": len(feature_order),
                    "interpretation": (
                        "Experimental transaction-level AML ranking score "
                        "from a synthetic-data model. It is not a calibrated "
                        "real-world probability or a confirmed finding."
                    ),
                },
            )

        except FileNotFoundError as exc:
            return InferenceResult(
                model_name=self.MODEL_NAME,
                status=ModelStatus.UNAVAILABLE,
                error=str(exc),
            )
        except Exception as exc:
            return InferenceResult(
                model_name=self.MODEL_NAME,
                status=ModelStatus.ERROR,
                error=f"{type(exc).__name__}: {exc}",
            )
