from pathlib import Path

import numpy as np
import polars as pl
import xgboost as xgb
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
)


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path("data/processed/features/xgboost")
MODEL_DIR = Path("data/processed/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_PATH = BASE_DIR / "train_xgboost_dataset.parquet"
VAL_PATH = BASE_DIR / "validation_xgboost_dataset.parquet"

MODEL_PATH = MODEL_DIR / "xgboost_aml_baseline.json"

TARGET = "Is_laundering"

RANDOM_STATE = 42


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 60)
print("XGBOOST AML BASELINE")
print("=" * 60)

print("\nLoading training dataset...")
train_df = pl.read_parquet(TRAIN_PATH)

print("Loading validation dataset...")
val_df = pl.read_parquet(VAL_PATH)

print(f"\nTrain shape:      {train_df.shape}")
print(f"Validation shape: {val_df.shape}")


# ============================================================
# IDENTIFY FEATURES
# ============================================================

NON_FEATURE_COLUMNS = {
    "transaction_id",
    TARGET,
}

feature_columns = [
    col for col in train_df.columns
    if col not in NON_FEATURE_COLUMNS
]

print(f"\nNumber of features: {len(feature_columns)}")

if len(feature_columns) != 71:
    raise ValueError(
        f"Expected 71 ML features, found {len(feature_columns)}"
    )


# ============================================================
# CONVERT TO NUMPY
# ============================================================

print("\nConverting datasets to float32 NumPy arrays...")
X_train = train_df.select(feature_columns).to_numpy().astype(
    np.float32,
    copy=False
)

y_train = train_df[TARGET].to_numpy().astype(
    np.int8,
    copy=False
)

X_val = val_df.select(feature_columns).to_numpy().astype(
    np.float32,
    copy=False
)

y_val = val_df[TARGET].to_numpy().astype(
    np.int8,
    copy=False
)
print(f"X_train: {X_train.shape}")
print(f"X_val:   {X_val.shape}")


# ============================================================
# CLASS IMBALANCE
# ============================================================

negative_count = int((y_train == 0).sum())
positive_count = int((y_train == 1).sum())

scale_pos_weight = negative_count / positive_count

print("\nClass distribution:")
print(f"Normal:      {negative_count:,}")
print(f"Laundering:  {positive_count:,}")
print(f"Positive rate: {positive_count / len(y_train) * 100:.6f}%")
print(f"scale_pos_weight: {scale_pos_weight:.2f}")


# ============================================================
# MODEL
# ============================================================

print("\nCreating XGBoost model...")

model = xgb.XGBClassifier(
    objective="binary:logistic",

    n_estimators=500,
    learning_rate=0.05,

    max_depth=8,
    min_child_weight=5,

    subsample=0.8,
    colsample_bytree=0.8,

    scale_pos_weight=scale_pos_weight,

    tree_method="hist",

    eval_metric=[
        "aucpr",
        "auc",
    ],

    random_state=RANDOM_STATE,

    n_jobs=-1,
)


# ============================================================
# TRAIN
# ============================================================

print("\nStarting training...")
print("This may take some time because the dataset has 6.65M rows.")
print("-" * 60)

model.fit(
    X_train,
    y_train,

    eval_set=[
        (X_train, y_train),
        (X_val, y_val),
    ],

    verbose=25,
)


# ============================================================
# VALIDATION PREDICTIONS
# ============================================================

print("\n" + "=" * 60)
print("VALIDATION RESULTS")
print("=" * 60)

val_prob = model.predict_proba(X_val)[:, 1]

val_pred = (val_prob >= 0.5).astype(np.int8)


# ============================================================
# METRICS
# ============================================================

pr_auc = average_precision_score(
    y_val,
    val_prob
)

roc_auc = roc_auc_score(
    y_val,
    val_prob
)

precision = precision_score(
    y_val,
    val_pred,
    zero_division=0
)

recall = recall_score(
    y_val,
    val_pred,
    zero_division=0
)

f1 = f1_score(
    y_val,
    val_pred,
    zero_division=0
)

print(f"PR-AUC:    {pr_auc:.6f}")
print(f"ROC-AUC:   {roc_auc:.6f}")
print(f"Precision:  {precision:.6f}")
print(f"Recall:     {recall:.6f}")
print(f"F1:         {f1:.6f}")


# ============================================================
# SAVE MODEL
# ============================================================

print("\nSaving model...")

model.save_model(MODEL_PATH)

print(f"Model saved to:")
print(MODEL_PATH)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

print("\n" + "=" * 60)
print("TOP 20 FEATURES")
print("=" * 60)

importance = model.feature_importances_

feature_importance = sorted(
    zip(feature_columns, importance),
    key=lambda x: x[1],
    reverse=True,
)

for rank, (feature, score) in enumerate(
    feature_importance[:20],
    start=1,
):
    print(
        f"{rank:2d}. {feature:<45} {score:.6f}"
    )


print("\n" + "=" * 60)
print("XGBOOST TRAINING COMPLETE")
print("=" * 60)