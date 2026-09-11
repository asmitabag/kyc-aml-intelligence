from pathlib import Path
import pandas as pd


# --------------------------------------------------
# Configuration
# --------------------------------------------------

DATA_DIR = Path("data/raw/samld")

# Find CSV files inside the SAML-D directory
csv_files = list(DATA_DIR.glob("*.csv"))


# --------------------------------------------------
# Check dataset files
# --------------------------------------------------

if not csv_files:
    raise FileNotFoundError(
        f"No CSV files found in {DATA_DIR.resolve()}"
    )

print("=" * 60)
print("SAML-D DATASET INSPECTION")
print("=" * 60)

print("\nFiles found:")

for file in csv_files:
    print(f" - {file}")


# --------------------------------------------------
# Inspect the first CSV
# --------------------------------------------------

data_file = csv_files[0]

print(f"\nInspecting: {data_file.name}")

# Read only a small sample first
df = pd.read_csv(data_file, nrows=1000)


# --------------------------------------------------
# Basic information
# --------------------------------------------------

print("\n" + "=" * 60)
print("SHAPE OF SAMPLE")
print("=" * 60)

print(f"Rows loaded: {len(df):,}")
print(f"Columns: {len(df.columns)}")


print("\n" + "=" * 60)
print("COLUMN NAMES")
print("=" * 60)

for column in df.columns:
    print(f" - {column}")


# --------------------------------------------------
# Data types
# --------------------------------------------------

print("\n" + "=" * 60)
print("DATA TYPES")
print("=" * 60)

print(df.dtypes)


# --------------------------------------------------
# Missing values
# --------------------------------------------------

print("\n" + "=" * 60)
print("MISSING VALUES")
print("=" * 60)

missing = df.isnull().sum()

for column, count in missing.items():
    print(f"{column}: {count}")


# --------------------------------------------------
# Basic statistics
# --------------------------------------------------

print("\n" + "=" * 60)
print("NUMERICAL SUMMARY")
print("=" * 60)

print(df.describe())


# --------------------------------------------------
# AML labels
# --------------------------------------------------

print("\n" + "=" * 60)
print("LAUNDERING LABEL DISTRIBUTION")
print("=" * 60)

print(df["Is_laundering"].value_counts(dropna=False))


print("\nLaundering type distribution:")

print(df["Laundering_type"].value_counts().head(20))


# --------------------------------------------------
# Categorical columns
# --------------------------------------------------

categorical_columns = [
    "Payment_currency",
    "Received_currency",
    "Sender_bank_location",
    "Receiver_bank_location",
    "Payment_type",
]

print("\n" + "=" * 60)
print("CATEGORICAL VALUE COUNTS")
print("=" * 60)

for column in categorical_columns:
    print(f"\n{column}:")
    print(df[column].value_counts().head(10))


# --------------------------------------------------
# Date/time inspection
# --------------------------------------------------

print("\n" + "=" * 60)
print("DATE/TIME")
print("=" * 60)

print("Earliest date:", df["Date"].min())
print("Latest date:", df["Date"].max())

print("\nSample timestamps:")

print(df[["Date", "Time"]].head(10).to_string(index=False))


print("\n" + "=" * 60)
print("FIRST 5 TRANSACTIONS")
print("=" * 60)

print(df.head().to_string(index=False))

print("\nInspection complete.")