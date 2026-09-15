from pathlib import Path

import polars as pl


# =========================================================
# Paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

GRAPH_DIR = PROJECT_ROOT / "data" / "processed" / "graph"
IDENTITY_DIR = PROJECT_ROOT / "data" / "processed" / "synthetic_identity"

OUTPUT_DIR = GRAPH_DIR / "heterogeneous"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# Load identity layer
# =========================================================

def load_identity_layer():

    mapping_path = IDENTITY_DIR / "identity_mapping.parquet"
    links_path = IDENTITY_DIR / "identity_links.parquet"

    if not mapping_path.exists():
        raise FileNotFoundError(mapping_path)

    if not links_path.exists():
        raise FileNotFoundError(links_path)

    mapping = pl.read_parquet(mapping_path)
    links = pl.read_parquet(links_path)

    print("\nIdentity mapping:")
    print(f"Records: {mapping.height:,}")

    print("\nIdentity links:")
    print(f"Relationships: {links.height:,}")

    return mapping, links


# =========================================================
# Build node tables
# =========================================================

def build_nodes(mapping: pl.DataFrame):

    # -----------------------------------------------------
    # Customer nodes
    # -----------------------------------------------------

    customers = (
        mapping
        .select("customer_id")
        .unique()
        .sort("customer_id")
    )

    # -----------------------------------------------------
    # Account nodes
    # -----------------------------------------------------

    accounts = (
        mapping
        .select("account_id")
        .unique()
        .sort("account_id")
    )

    # -----------------------------------------------------
    # Device nodes
    # -----------------------------------------------------

    devices = (
        mapping
        .select("device_id")
        .unique()
        .sort("device_id")
    )

    # -----------------------------------------------------
    # Address nodes
    # -----------------------------------------------------

    addresses = (
        mapping
        .select("address_id")
        .unique()
        .sort("address_id")
    )

    # -----------------------------------------------------
    # Document nodes
    # -----------------------------------------------------

    documents = (
        mapping
        .select("document_id")
        .unique()
        .sort("document_id")
    )

    nodes = {
        "customer": customers,
        "account": accounts,
        "device": devices,
        "address": addresses,
        "document": documents,
    }

    print("\nNode counts:")

    for node_type, table in nodes.items():
        print(f"{node_type:10s}: {table.height:,}")

    return nodes


# =========================================================
# Build identity edges
# =========================================================

def build_identity_edges(links: pl.DataFrame):

    # -----------------------------------------------------
    # CUSTOMER -> ACCOUNT
    # -----------------------------------------------------

    owns = (
        links
        .filter(
            (pl.col("source_type") == "CUSTOMER")
            & (pl.col("target_type") == "ACCOUNT")
        )
        .select([
            pl.col("source_id").alias("customer_id"),
            pl.col("target_id").alias("account_id"),
        ])
        .unique()
    )

    # -----------------------------------------------------
    # CUSTOMER -> DEVICE
    # -----------------------------------------------------

    uses = (
        links
        .filter(
            (pl.col("source_type") == "CUSTOMER")
            & (pl.col("target_type") == "DEVICE")
        )
        .select([
            pl.col("source_id").alias("customer_id"),
            pl.col("target_id").alias("device_id"),
        ])
        .unique()
    )

    # -----------------------------------------------------
    # CUSTOMER -> ADDRESS
    # -----------------------------------------------------

    lives_at = (
        links
        .filter(
            (pl.col("source_type") == "CUSTOMER")
            & (pl.col("target_type") == "ADDRESS")
        )
        .select([
            pl.col("source_id").alias("customer_id"),
            pl.col("target_id").alias("address_id"),
        ])
        .unique()
    )

    # -----------------------------------------------------
    # CUSTOMER -> DOCUMENT
    # -----------------------------------------------------

    submitted = (
        links
        .filter(
            (pl.col("source_type") == "CUSTOMER")
            & (pl.col("target_type") == "DOCUMENT")
        )
        .select([
            pl.col("source_id").alias("customer_id"),
            pl.col("target_id").alias("document_id"),
        ])
        .unique()
    )

    edges = {
        "owns": owns,
        "uses": uses,
        "lives_at": lives_at,
        "submitted": submitted,
    }

    print("\nIdentity edge counts:")

    for edge_type, table in edges.items():
        print(f"{edge_type:12s}: {table.height:,}")

    return edges


# =========================================================
# Validate identity graph
# =========================================================

def validate_identity_graph(nodes, edges):

    print("\nRunning identity graph validation...")

    # Every account should have exactly one customer owner
    account_owner_counts = (
        edges["owns"]
        .group_by("account_id")
        .len()
    )

    invalid_accounts = account_owner_counts.filter(
        pl.col("len") != 1
    )

    if invalid_accounts.height > 0:
        raise ValueError(
            f"Found {invalid_accounts.height:,} accounts "
            "with an invalid number of owners."
        )

    # Every customer should have one device
    customer_device_counts = (
        edges["uses"]
        .group_by("customer_id")
        .len()
    )

    invalid_devices = customer_device_counts.filter(
        pl.col("len") != 1
    )

    if invalid_devices.height > 0:
        raise ValueError(
            f"Found {invalid_devices.height:,} customers "
            "with an invalid number of devices."
        )

    # Every customer should have one address
    customer_address_counts = (
        edges["lives_at"]
        .group_by("customer_id")
        .len()
    )

    invalid_addresses = customer_address_counts.filter(
        pl.col("len") != 1
    )

    if invalid_addresses.height > 0:
        raise ValueError(
            f"Found {invalid_addresses.height:,} customers "
            "with an invalid number of addresses."
        )

    # Every customer should have one document
    customer_document_counts = (
        edges["submitted"]
        .group_by("customer_id")
        .len()
    )

    invalid_documents = customer_document_counts.filter(
        pl.col("len") != 1
    )

    if invalid_documents.height > 0:
        raise ValueError(
            f"Found {invalid_documents.height:,} customers "
            "with an invalid number of documents."
        )

    print("Identity graph validation PASSED.")


# =========================================================
# Save graph components
# =========================================================

def save_graph_components(nodes, edges):

    print("\nSaving graph components...")

    # Nodes
    for node_type, table in nodes.items():

        path = OUTPUT_DIR / f"{node_type}_nodes.parquet"

        table.write_parquet(path)

        print(f"Saved: {path}")

    # Identity edges
    for edge_type, table in edges.items():

        path = OUTPUT_DIR / f"{edge_type}_edges.parquet"

        table.write_parquet(path)

        print(f"Saved: {path}")


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("HETEROGENEOUS GRAPH CONSTRUCTION")
    print("=" * 60)

    mapping, links = load_identity_layer()

    nodes = build_nodes(mapping)

    identity_edges = build_identity_edges(links)

    validate_identity_graph(
        nodes,
        identity_edges,
    )

    save_graph_components(
        nodes,
        identity_edges,
    )

    print("\n" + "=" * 60)
    print("HETEROGENEOUS IDENTITY GRAPH COMPLETE")
    print("=" * 60)