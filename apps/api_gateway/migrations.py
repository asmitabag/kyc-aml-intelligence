from collections.abc import Iterable

from sqlalchemy import Engine, inspect, text


SCHEMA_VERSION = 2


def _columns(engine: Engine, table: str) -> set[str]:
    return {column["name"] for column in inspect(engine).get_columns(table)}


def _add_columns(engine: Engine, table: str, definitions: Iterable[tuple[str, str]]) -> None:
    existing = _columns(engine, table)
    with engine.begin() as connection:
        for name, definition in definitions:
            if name not in existing:
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))


def migrate_database(engine: Engine) -> int:
    """Apply additive SQLite migrations without rewriting existing tables."""

    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(version INTEGER PRIMARY KEY, applied_at DATETIME NOT NULL)"
            )
        )

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "customers" not in tables:
        return 0

    _add_columns(
        engine,
        "customers",
        [("customer_type", "VARCHAR"), ("data_origin", "VARCHAR")],
    )
    _add_columns(
        engine,
        "accounts",
        [("account_type", "VARCHAR"), ("status", "VARCHAR"), ("balance", "FLOAT"), ("currency", "VARCHAR")],
    )
    _add_columns(
        engine,
        "transactions",
        [
            ("to_account_id", "VARCHAR"),
            ("data_origin", "VARCHAR"),
            ("amount_decimal", "NUMERIC(18, 2)"),
        ],
    )
    _add_columns(
        engine,
        "risk_assessments",
        [
            ("gnn_risk", "FLOAT"),
            ("xgboost_risk", "FLOAT"),
            ("final_risk", "FLOAT"),
            ("risk_level", "VARCHAR"),
            ("top_risk_factors", "JSON"),
            ("gnn_model_version", "VARCHAR"),
            ("xgboost_model_version", "VARCHAR"),
            ("updated_at", "DATETIME"),
        ],
    )
    _add_columns(engine, "alerts", [("assessment_id", "VARCHAR"), ("reason_code", "VARCHAR")])
    _add_columns(
        engine,
        "sar_drafts",
        [("alert_id", "VARCHAR"), ("review_status", "VARCHAR")],
    )

    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE transactions SET amount_decimal = CAST(amount AS NUMERIC) "
                "WHERE amount_decimal IS NULL AND amount IS NOT NULL"
            )
        )
        connection.execute(
            text(
                "UPDATE customers SET customer_type = 'INDIVIDUAL' "
                "WHERE customer_type IS NULL"
            )
        )
        connection.execute(
            text(
                "UPDATE customers SET data_origin = 'CONSENTED_DEMO' "
                "WHERE data_origin IS NULL"
            )
        )
        connection.execute(
            text(
                "UPDATE transactions SET data_origin = 'SYNTHETIC' "
                "WHERE data_origin IS NULL"
            )
        )
        connection.execute(
            text(
                "UPDATE sar_drafts SET review_status = 'DRAFT' "
                "WHERE review_status IS NULL"
            )
        )
        connection.execute(
            text("CREATE INDEX IF NOT EXISTS ix_alerts_assessment_id ON alerts (assessment_id)")
        )
        connection.execute(
            text("CREATE INDEX IF NOT EXISTS ix_sar_drafts_alert_id ON sar_drafts (alert_id)")
        )
        connection.execute(
            text(
                "INSERT OR IGNORE INTO schema_migrations(version, applied_at) "
                "VALUES (:version, CURRENT_TIMESTAMP)"
            ),
            {"version": SCHEMA_VERSION},
        )
    return SCHEMA_VERSION
