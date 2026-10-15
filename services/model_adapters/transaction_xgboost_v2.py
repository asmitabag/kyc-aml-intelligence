from pathlib import Path
from typing import Any
import json

import joblib
import pandas as pd
import xgboost as xgb

from services.model_adapters.contracts import InferenceResult, ModelStatus


class TransactionXGBoostV2Adapter:
    """Adapter for the portable synthetic-data transaction AML model."""

    MODEL_NAME = "xgboost_aml_v2"
    MODEL_VERSION = "2.1.0"

    def __init__(self) -> None:
        root = Path(__file__).resolve().parents[2]
        artifact_dir = root / "artifacts" / "aml_xgboost_v2"
        portable_dir = artifact_dir / "portable"

        self.preprocessor_path = portable_dir / "preprocessor.joblib"
        self.booster_path = portable_dir / "xgboost_booster.json"
        self.schema_path = artifact_dir / "feature_schema.json"

        self._preprocessor = None
        self._booster = None
        self._schema = None

    def _load(self) -> None:
        if (
            self._preprocessor is not None
            and self._booster is not None
            and self._schema is not None
        ):
            return

        for path in (
            self.preprocessor_path,
            self.booster_path,
            self.schema_path,
        ):
            if not path.is_file():
                raise FileNotFoundError(f"Required model file not found: {path}")

        with self.schema_path.open("r", encoding="utf-8-sig") as file:
            schema = json.load(file)

        preprocessor = joblib.load(self.preprocessor_path)

        booster = xgb.Booster()
        booster.load_model(str(self.booster_path))

        self._preprocessor = preprocessor
        self._booster = booster
        self._schema = schema

    def predict_transaction(
        self, row: dict[str, Any]
    ) -> InferenceResult[dict[str, Any]]:
        try:
            self._load()

            assert self._preprocessor is not None
            assert self._booster is not None
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

            # Apply the saved preprocessing, then predict with native XGBoost.
            transformed = self._preprocessor.transform(X)
            dmatrix = xgb.DMatrix(transformed)
            score = float(self._booster.predict(dmatrix)[0])

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