from pathlib import Path
import pandas as pd


INPUT_METADATA = Path(
    "data/processed/midv_base/metadata.csv"
)

REGION_METADATA = Path(
    "data/processed/document_regions/metadata.csv"
)

OUTPUT_ROOT = Path(
    "data/processed/splits"
)

OUTPUT_ROOT.mkdir(
    parents=True,
    exist_ok=True
)


TRAIN_TYPES = [
    "01_alb_id",
    "02_aut_drvlic_new",
    "03_aut_id_old",
    "04_aut_id",
]

VAL_TYPES = [
    "05_aze_passport",
]

TEST_TYPES = [
    "06_bra_passport",
]


base = pd.read_csv(
    INPUT_METADATA
)

regions = pd.read_csv(
    REGION_METADATA
)


metadata = base.merge(
    regions[
        [
            "sample_id",
            "document_mask",
        ]
    ],
    on="sample_id",
    how="inner",
)


train_df = metadata[
    metadata["document_type"].isin(
        TRAIN_TYPES
    )
].copy()

val_df = metadata[
    metadata["document_type"].isin(
        VAL_TYPES
    )
].copy()

test_df = metadata[
    metadata["document_type"].isin(
        TEST_TYPES
    )
].copy()


train_df["split"] = "train"
val_df["split"] = "val"
test_df["split"] = "test"


train_df.to_csv(
    OUTPUT_ROOT / "train.csv",
    index=False
)

val_df.to_csv(
    OUTPUT_ROOT / "val.csv",
    index=False
)

test_df.to_csv(
    OUTPUT_ROOT / "test.csv",
    index=False
)


combined = pd.concat(
    [
        train_df,
        val_df,
        test_df,
    ],
    ignore_index=True
)


combined.to_csv(
    OUTPUT_ROOT / "all_splits.csv",
    index=False
)


print("\n------------------------------")
print("DOCUMENT-LEVEL SPLIT COMPLETE")
print("------------------------------")

print(
    f"Training samples:   "
    f"{len(train_df)}"
)

print(
    f"Validation samples: "
    f"{len(val_df)}"
)

print(
    f"Test samples:       "
    f"{len(test_df)}"
)

print(
    f"Total:              "
    f"{len(combined)}"
)


print("\nTRAIN:")
print(
    train_df[
        "document_type"
    ].value_counts()
)


print("\nVALIDATION:")
print(
    val_df[
        "document_type"
    ].value_counts()
)


print("\nTEST:")
print(
    test_df[
        "document_type"
    ].value_counts()
)