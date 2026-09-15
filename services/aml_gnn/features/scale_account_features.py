from pathlib import Path

import joblib
import numpy as np
import polars as pl
from sklearn.preprocessing import StandardScaler


BASE_DIR = Path(__file__).resolve().parents[3]

INPUT_DIR = BASE_DIR / "data" / "processed" / "features" / "aligned"
OUTPUT_DIR = BASE_DIR / "data" / "processed" / "features" / "scaled"

SCALER_PATH = OUTPUT_DIR / "account_feature_scaler.joblib"

SPLITS = ["train", "validation", "test"]

ID_COLUMN = "account_id"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # 1. Load aligned account features
    # ---------------------------------------------------------
    train = pl.read_parquet(
        INPUT_DIR / "train_account_features_aligned.parquet"
    )
    validation = pl.read_parquet(
        INPUT_DIR / "validation_account_features_aligned.parquet"
    )
    test = pl.read_parquet(
        INPUT_DIR / "test_account_features_aligned.parquet"
    )

    print("Loaded:")
    print(f"  Train:      {train.shape}")
    print(f"  Validation: {validation.shape}")
    print(f"  Test:       {test.shape}")

    # ---------------------------------------------------------
    # 2. Identify feature columns
    # ---------------------------------------------------------
    feature_columns = [
        column for column in train.columns
        if column != ID_COLUMN
    ]

    print(f"\nFeature count: {len(feature_columns)}")
    print("Features:")
    for column in feature_columns:
        print(f"  - {column}")

    # ---------------------------------------------------------
    # 3. Convert training features to NumPy
    # ---------------------------------------------------------
    X_train = train.select(feature_columns).to_numpy()

    if not np.isfinite(X_train).all():
        raise ValueError("Training features contain NaN or infinite values.")

    # ---------------------------------------------------------
    # 4. Fit scaler ONLY on training data
    # ---------------------------------------------------------
    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(X_train)

    print("\nScaler fitted on TRAIN only.")

    # ---------------------------------------------------------
    # 5. Transform validation and test using same scaler
    # ---------------------------------------------------------
    X_validation = validation.select(feature_columns).to_numpy()
    X_test = test.select(feature_columns).to_numpy()

    if not np.isfinite(X_validation).all():
        raise ValueError("Validation features contain NaN or infinite values.")

    if not np.isfinite(X_test).all():
        raise ValueError("Test features contain NaN or infinite values.")

    X_validation_scaled = scaler.transform(X_validation)
    X_test_scaled = scaler.transform(X_test)

    # ---------------------------------------------------------
    # 6. Convert back to Polars
    # ---------------------------------------------------------
    train_scaled = pl.DataFrame(
        X_train_scaled,
        schema=feature_columns,
        orient="row",
    ).with_columns(
        train[ID_COLUMN]
    ).select([ID_COLUMN] + feature_columns)

    validation_scaled = pl.DataFrame(
        X_validation_scaled,
        schema=feature_columns,
        orient="row",
    ).with_columns(
        validation[ID_COLUMN]
    ).select([ID_COLUMN] + feature_columns)

    test_scaled = pl.DataFrame(
        X_test_scaled,
        schema=feature_columns,
        orient="row",
    ).with_columns(
        test[ID_COLUMN]
    ).select([ID_COLUMN] + feature_columns)

    # ---------------------------------------------------------
    # 7. Save scaled features
    # ---------------------------------------------------------
    train_path = OUTPUT_DIR / "train_account_features_scaled.parquet"
    validation_path = OUTPUT_DIR / "validation_account_features_scaled.parquet"
    test_path = OUTPUT_DIR / "test_account_features_scaled.parquet"

    train_scaled.write_parquet(train_path)
    validation_scaled.write_parquet(validation_path)
    test_scaled.write_parquet(test_path)

    # ---------------------------------------------------------
    # 8. Save scaler
    # ---------------------------------------------------------
    joblib.dump(
        {
            "scaler": scaler,
            "feature_columns": feature_columns,
            "id_column": ID_COLUMN,
        },
        SCALER_PATH,
    )

    # ---------------------------------------------------------
    # 9. Validation
    # ---------------------------------------------------------
    for name, df in [
        ("train", train_scaled),
        ("validation", validation_scaled),
        ("test", test_scaled),
    ]:
        if df.height == 0:
            raise ValueError(f"{name} scaled dataset is empty.")

        if df[ID_COLUMN].n_unique() != df.height:
            raise ValueError(
                f"{name} contains duplicate account IDs."
            )

        values = df.select(feature_columns).to_numpy()

        if not np.isfinite(values).all():
            raise ValueError(
                f"{name} scaled features contain NaN or infinite values."
            )

    print("\nValidation PASSED.")

    print("\nSaved:")
    print(f"  {train_path}")
    print(f"  {validation_path}")
    print(f"  {test_path}")
    print(f"  {SCALER_PATH}")

    # ---------------------------------------------------------
    # 10. Show training statistics
    # ---------------------------------------------------------
    train_means = X_train_scaled.mean(axis=0)
    train_stds = X_train_scaled.std(axis=0)

    print("\nTraining scaled statistics:")
    print(f"  Maximum absolute mean: {np.abs(train_means).max():.6f}")
    print(f"  Minimum std:           {train_stds.min():.6f}")
    print(f"  Maximum std:           {train_stds.max():.6f}")


if __name__ == "__main__":
    main()