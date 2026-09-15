from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[3]

ACCOUNT_FEATURE_DIR = (
    BASE_DIR / "data" / "processed" / "account_features"
)

OUTPUT_DIR = (
    BASE_DIR / "data" / "processed" / "synthetic_identity"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SETTINGS
# ============================================================

SEED = 42

# Approximately 2% of accounts participate in synthetic
# identity structures.
RING_ACCOUNT_FRACTION = 0.02

MIN_RING_SIZE = 4
MAX_RING_SIZE = 8

# Different identity-reuse patterns.
PATTERNS = [
    "shared_device",
    "shared_document",
    "shared_device_document",
    "shared_device_address",
    "shared_all",
]

# Legitimate shared-address groups.
HARD_NEGATIVE_FRACTION = 0.02

MIN_FAMILY_SIZE = 2
MAX_FAMILY_SIZE = 4


# ============================================================
# LOAD ACCOUNT IDS
# ============================================================

def load_account_ids():

    account_ids = set()

    for split in ["train", "validation", "test"]:

        path = (
            ACCOUNT_FEATURE_DIR
            / f"{split}_account_features.parquet"
        )

        print(f"Loading: {path}")

        df = pd.read_parquet(
            path,
            columns=["account_id"],
        )

        account_ids.update(
            df["account_id"].astype(int)
        )

    account_ids = sorted(account_ids)

    print(
        f"\nUnique accounts: {len(account_ids):,}"
    )

    return account_ids


# ============================================================
# CREATE BASE IDENTITY
# ============================================================

def create_base_identity(account_ids):

    records = []

    for i, account_id in enumerate(account_ids, start=1):

        records.append(
            {
                "account_id": int(account_id),

                # All graph entity IDs are strings.
                "customer_id": f"C{i:08d}",
                "device_id": f"D{i:08d}",
                "address_id": f"ADDR{i:08d}",
                "document_id": f"DOC{i:08d}",

                "synthetic_ring_label": 0,
                "synthetic_ring_id": "",

                "identity_pattern": "normal",

                "hard_negative_family_label": 0,
                "hard_negative_family_id": "",
            }
        )

    return pd.DataFrame(records)


# ============================================================
# INJECT SYNTHETIC IDENTITY RINGS
# ============================================================

def inject_identity_rings(identity_df, rng):

    account_ids = identity_df[
        "account_id"
    ].to_numpy(copy=True)

    target_count = int(
        len(account_ids)
        * RING_ACCOUNT_FRACTION
    )

    rng.shuffle(account_ids)

    selected = account_ids[:target_count]

    ring_records = []

    cursor = 0
    ring_number = 1

    while cursor < len(selected):

        remaining = len(selected) - cursor

        if remaining < MIN_RING_SIZE:
            break

        ring_size = int(
            rng.integers(
                MIN_RING_SIZE,
                min(MAX_RING_SIZE, remaining) + 1,
            )
        )

        members = selected[
            cursor:cursor + ring_size
        ]

        pattern = rng.choice(PATTERNS)

        ring_id = f"RING_{ring_number:05d}"

        shared_device = (
            f"RING_DEVICE_{ring_number:05d}"
        )

        shared_document = (
            f"RING_DOC_{ring_number:05d}"
        )

        shared_address = (
            f"RING_ADDR_{ring_number:05d}"
        )

        member_mask = identity_df[
            "account_id"
        ].isin(members)

        # Mark ring membership.
        identity_df.loc[
            member_mask,
            "synthetic_ring_label"
        ] = 1

        identity_df.loc[
            member_mask,
            "synthetic_ring_id"
        ] = ring_id

        identity_df.loc[
            member_mask,
            "identity_pattern"
        ] = pattern

        # ----------------------------------------------------
        # Apply device reuse
        # ----------------------------------------------------

        if pattern in [
            "shared_device",
            "shared_device_document",
            "shared_device_address",
            "shared_all",
        ]:

            identity_df.loc[
                member_mask,
                "device_id"
            ] = shared_device

        # ----------------------------------------------------
        # Apply document reuse
        # ----------------------------------------------------

        if pattern in [
            "shared_document",
            "shared_device_document",
            "shared_all",
        ]:

            identity_df.loc[
                member_mask,
                "document_id"
            ] = shared_document

        # ----------------------------------------------------
        # Apply address reuse
        # ----------------------------------------------------

        if pattern in [
            "shared_device_address",
            "shared_all",
        ]:

            identity_df.loc[
                member_mask,
                "address_id"
            ] = shared_address

        # ----------------------------------------------------
        # Store ring metadata
        # ----------------------------------------------------

        ring_records.append(
            {
                "ring_id": ring_id,
                "ring_size": ring_size,
                "identity_pattern": pattern,

                "shared_device": (
                    shared_device
                    if pattern in [
                        "shared_device",
                        "shared_device_document",
                        "shared_device_address",
                        "shared_all",
                    ]
                    else ""
                ),

                "shared_document": (
                    shared_document
                    if pattern in [
                        "shared_document",
                        "shared_device_document",
                        "shared_all",
                    ]
                    else ""
                ),

                "shared_address": (
                    shared_address
                    if pattern in [
                        "shared_device_address",
                        "shared_all",
                    ]
                    else ""
                ),
            }
        )

        ring_number += 1
        cursor += ring_size

    rings_df = pd.DataFrame(ring_records)

    return identity_df, rings_df


# ============================================================
# LEGITIMATE SHARED-ADDRESS GROUPS
# ============================================================

def inject_hard_negatives(identity_df, rng):

    eligible = identity_df[
        identity_df["synthetic_ring_label"] == 0
    ]["account_id"].to_numpy(copy=True)

    target_count = int(
        len(eligible)
        * HARD_NEGATIVE_FRACTION
    )

    rng.shuffle(eligible)

    selected = eligible[:target_count]

    records = []

    cursor = 0
    family_number = 1

    while cursor < len(selected):

        remaining = len(selected) - cursor

        if remaining < MIN_FAMILY_SIZE:
            break

        family_size = int(
            rng.integers(
                MIN_FAMILY_SIZE,
                min(MAX_FAMILY_SIZE, remaining) + 1,
            )
        )

        members = selected[
            cursor:cursor + family_size
        ]

        family_id = (
            f"FAMILY_{family_number:05d}"
        )

        shared_address = (
            f"FAMILY_ADDR_{family_number:05d}"
        )

        mask = identity_df[
            "account_id"
        ].isin(members)

        # Legitimate family members share only an address.
        identity_df.loc[
            mask,
            "address_id"
        ] = shared_address

        identity_df.loc[
            mask,
            "hard_negative_family_label"
        ] = 1

        identity_df.loc[
            mask,
            "hard_negative_family_id"
        ] = family_id

        records.append(
            {
                "family_id": family_id,
                "family_size": family_size,
                "shared_address": shared_address,
            }
        )

        family_number += 1
        cursor += family_size

    families_df = pd.DataFrame(records)

    return identity_df, families_df


# ============================================================
# BUILD GRAPH-READY IDENTITY RELATIONSHIPS
# ============================================================

def build_relationships(identity_df):

    links = []

    for row in identity_df.itertuples(index=False):

        # IMPORTANT:
        # Every graph entity ID is explicitly converted to str.
        customer = str(row.customer_id)
        account = str(row.account_id)
        device = str(row.device_id)
        address = str(row.address_id)
        document = str(row.document_id)

        # ----------------------------------------------------
        # CUSTOMER -> ACCOUNT
        # ----------------------------------------------------

        links.append(
            {
                "source_id": customer,
                "target_id": account,

                "source_type": "CUSTOMER",
                "target_type": "ACCOUNT",

                "relationship": "owns",

                "synthetic_link": 0,
                "ring_id": "",

                "account_id": int(row.account_id),
            }
        )

        # ----------------------------------------------------
        # CUSTOMER -> DEVICE
        # ----------------------------------------------------

        device_is_synthetic = (
            row.synthetic_ring_label == 1
            and row.identity_pattern in [
                "shared_device",
                "shared_device_document",
                "shared_device_address",
                "shared_all",
            ]
        )

        links.append(
            {
                "source_id": customer,
                "target_id": device,

                "source_type": "CUSTOMER",
                "target_type": "DEVICE",

                "relationship": "uses",

                "synthetic_link": int(
                    device_is_synthetic
                ),

                "ring_id": str(
                    row.synthetic_ring_id
                ),

                "account_id": int(row.account_id),
            }
        )

        # ----------------------------------------------------
        # CUSTOMER -> ADDRESS
        # ----------------------------------------------------

        address_is_synthetic = (
            row.synthetic_ring_label == 1
            and row.identity_pattern in [
                "shared_device_address",
                "shared_all",
            ]
        )

        links.append(
            {
                "source_id": customer,
                "target_id": address,

                "source_type": "CUSTOMER",
                "target_type": "ADDRESS",

                "relationship": "lives_at",

                "synthetic_link": int(
                    address_is_synthetic
                ),

                "ring_id": str(
                    row.synthetic_ring_id
                ),

                "account_id": int(row.account_id),
            }
        )

        # ----------------------------------------------------
        # CUSTOMER -> DOCUMENT
        # ----------------------------------------------------

        document_is_synthetic = (
            row.synthetic_ring_label == 1
            and row.identity_pattern in [
                "shared_document",
                "shared_device_document",
                "shared_all",
            ]
        )

        links.append(
            {
                "source_id": customer,
                "target_id": document,

                "source_type": "CUSTOMER",
                "target_type": "DOCUMENT",

                "relationship": "submitted",

                "synthetic_link": int(
                    document_is_synthetic
                ),

                "ring_id": str(
                    row.synthetic_ring_id
                ),

                "account_id": int(row.account_id),
            }
        )

    links_df = pd.DataFrame(links)

    # --------------------------------------------------------
    # Explicitly enforce correct dtypes before Parquet export.
    # --------------------------------------------------------

    links_df["source_id"] = (
        links_df["source_id"].astype(str)
    )

    links_df["target_id"] = (
        links_df["target_id"].astype(str)
    )

    links_df["source_type"] = (
        links_df["source_type"].astype(str)
    )

    links_df["target_type"] = (
        links_df["target_type"].astype(str)
    )

    links_df["relationship"] = (
        links_df["relationship"].astype(str)
    )

    links_df["ring_id"] = (
        links_df["ring_id"].astype(str)
    )

    links_df["synthetic_link"] = (
        links_df["synthetic_link"].astype("int8")
    )

    links_df["account_id"] = (
        links_df["account_id"].astype("int64")
    )

    return links_df


# ============================================================
# VALIDATE IDENTITY STRUCTURE
# ============================================================

def validate_identity_layer(
    identity_df,
    links_df,
    rings_df,
    families_df,
):

    print("\n" + "=" * 70)
    print("VALIDATING SYNTHETIC IDENTITY LAYER")
    print("=" * 70)

    # --------------------------------------------------------
    # Basic counts
    # --------------------------------------------------------

    print(
        f"\nAccounts: "
        f"{len(identity_df):,}"
    )

    print(
        f"Identity relationships: "
        f"{len(links_df):,}"
    )

    print(
        f"Synthetic rings: "
        f"{len(rings_df):,}"
    )

    print(
        f"Hard-negative families: "
        f"{len(families_df):,}"
    )

    # --------------------------------------------------------
    # Check duplicate account mapping
    # --------------------------------------------------------

    duplicate_accounts = (
        identity_df["account_id"]
        .duplicated()
        .sum()
    )

    print(
        f"\nDuplicate account mappings: "
        f"{duplicate_accounts}"
    )

    # --------------------------------------------------------
    # Check required entity IDs
    # --------------------------------------------------------

    required_columns = [
        "account_id",
        "customer_id",
        "device_id",
        "address_id",
        "document_id",
    ]

    missing_values = (
        identity_df[required_columns]
        .isna()
        .sum()
        .sum()
    )

    print(
        f"Missing identity values: "
        f"{missing_values}"
    )

    # --------------------------------------------------------
    # Ring pattern distribution
    # --------------------------------------------------------

    if not rings_df.empty:

        print("\nSynthetic identity patterns:")

        print(
            rings_df[
                "identity_pattern"
            ].value_counts()
        )

    # --------------------------------------------------------
    # Verify shared identity artifacts
    # --------------------------------------------------------

    print("\nShared identity artifacts:")

    ring_accounts = identity_df[
        identity_df["synthetic_ring_label"] == 1
    ]

    if not ring_accounts.empty:

        shared_devices = (
            ring_accounts["device_id"]
            .value_counts()
        )

        shared_documents = (
            ring_accounts["document_id"]
            .value_counts()
        )

        shared_addresses = (
            ring_accounts["address_id"]
            .value_counts()
        )

        print(
            "Devices used by multiple ring accounts:",
            int((shared_devices > 1).sum()),
        )

        print(
            "Documents used by multiple ring accounts:",
            int((shared_documents > 1).sum()),
        )

        print(
            "Addresses used by multiple ring accounts:",
            int((shared_addresses > 1).sum()),
        )

    # --------------------------------------------------------
    # Validation assertions
    # --------------------------------------------------------

    assert duplicate_accounts == 0, (
        "Duplicate account mappings detected."
    )

    assert missing_values == 0, (
        "Missing identity values detected."
    )

    assert len(links_df) == (
        len(identity_df) * 4
    ), (
        "Expected exactly four identity relationships "
        "per account."
    )

    assert (
        links_df["source_id"].dtype == object
    )

    assert (
        links_df["target_id"].dtype == object
    )

    print("\nValidation PASSED.")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("FUNCTIONAL SYNTHETIC IDENTITY GENERATOR")
    print("=" * 70)

    rng = np.random.default_rng(SEED)

    # --------------------------------------------------------
    # 1. Load accounts
    # --------------------------------------------------------

    account_ids = load_account_ids()

    # --------------------------------------------------------
    # 2. Create normal identity mapping
    # --------------------------------------------------------

    identity_df = create_base_identity(
        account_ids
    )

    print(
        f"\nBase identity records: "
        f"{len(identity_df):,}"
    )

    # --------------------------------------------------------
    # 3. Create synthetic identity rings
    # --------------------------------------------------------

    identity_df, rings_df = (
        inject_identity_rings(
            identity_df,
            rng,
        )
    )

    # --------------------------------------------------------
    # 4. Create legitimate hard negatives
    # --------------------------------------------------------

    identity_df, families_df = (
        inject_hard_negatives(
            identity_df,
            rng,
        )
    )

    # --------------------------------------------------------
    # 5. Build actual graph relationships
    # --------------------------------------------------------

    links_df = build_relationships(
        identity_df
    )

    # --------------------------------------------------------
    # 6. Validate before saving
    # --------------------------------------------------------

    validate_identity_layer(
        identity_df,
        links_df,
        rings_df,
        families_df,
    )

    # --------------------------------------------------------
    # 7. Save outputs
    # --------------------------------------------------------

    identity_path = (
        OUTPUT_DIR
        / "identity_mapping.parquet"
    )

    links_path = (
        OUTPUT_DIR
        / "identity_links.parquet"
    )

    rings_path = (
        OUTPUT_DIR
        / "synthetic_rings.parquet"
    )

    families_path = (
        OUTPUT_DIR
        / "hard_negative_families.parquet"
    )

    identity_df.to_parquet(
        identity_path,
        index=False,
    )

    links_df.to_parquet(
        links_path,
        index=False,
    )

    rings_df.to_parquet(
        rings_path,
        index=False,
    )

    families_df.to_parquet(
        families_path,
        index=False,
    )

    # --------------------------------------------------------
    # 8. Final statistics
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("GENERATED OUTPUTS")
    print("=" * 70)

    print(
        f"\nIdentity mapping:"
        f"\n{identity_path}"
    )

    print(
        f"\nIdentity links:"
        f"\n{links_path}"
    )

    print(
        f"\nSynthetic rings:"
        f"\n{rings_path}"
    )

    print(
        f"\nHard-negative families:"
        f"\n{families_path}"
    )

    print("\n" + "=" * 70)
    print("STATISTICS")
    print("=" * 70)

    print(
        f"\nTotal accounts: "
        f"{len(identity_df):,}"
    )

    print(
        f"Synthetic-ring accounts: "
        f"{identity_df['synthetic_ring_label'].sum():,}"
    )

    print(
        f"Unique synthetic rings: "
        f"{len(rings_df):,}"
    )

    print(
        f"Hard-negative accounts: "
        f"{identity_df['hard_negative_family_label'].sum():,}"
    )

    print(
        f"Hard-negative families: "
        f"{len(families_df):,}"
    )

    print(
        f"Identity graph relationships: "
        f"{len(links_df):,}"
    )

    # --------------------------------------------------------
    # Example ring
    # --------------------------------------------------------

    if not rings_df.empty:

        example_ring = (
            rings_df.iloc[0]["ring_id"]
        )

        print(
            "\nExample synthetic identity ring:"
        )

        print(
            identity_df[
                identity_df["synthetic_ring_id"]
                == example_ring
            ][
                [
                    "account_id",
                    "customer_id",
                    "device_id",
                    "address_id",
                    "document_id",
                    "identity_pattern",
                    "synthetic_ring_id",
                ]
            ].to_string(index=False)
        )

    # --------------------------------------------------------
    # Example graph links
    # --------------------------------------------------------

    print(
        "\nExample identity graph relationships:"
    )

    print(
        links_df.head(12).to_string(
            index=False
        )
    )

    print("\n" + "=" * 70)
    print(
        "SYNTHETIC IDENTITY GENERATION COMPLETE"
    )
    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()