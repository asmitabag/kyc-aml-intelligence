import sqlite3

from sqlalchemy import create_engine, text

from apps.api_gateway.migrations import SCHEMA_VERSION, migrate_database


def test_additive_migration_preserves_legacy_cases_feedback_and_transactions(tmp_path):
    source = tmp_path / "previous-schema.db"
    connection = sqlite3.connect(source)
    connection.executescript(
        """
        CREATE TABLE customers (
            customer_id VARCHAR PRIMARY KEY,
            full_name VARCHAR NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        );
        CREATE TABLE accounts (
            account_id VARCHAR PRIMARY KEY,
            customer_id VARCHAR NOT NULL
        );
        CREATE TABLE transactions (
            transaction_id VARCHAR PRIMARY KEY,
            account_id VARCHAR NOT NULL,
            direction VARCHAR NOT NULL,
            amount FLOAT NOT NULL,
            occurred_at DATETIME NOT NULL
        );
        CREATE TABLE risk_assessments (
            assessment_id VARCHAR PRIMARY KEY,
            customer_id VARCHAR NOT NULL,
            kyc_risk FLOAT NOT NULL,
            aml_risk FLOAT NOT NULL,
            fused_risk FLOAT NOT NULL,
            created_at DATETIME NOT NULL
        );
        CREATE TABLE alerts (
            alert_id VARCHAR PRIMARY KEY,
            customer_id VARCHAR NOT NULL,
            alert_type VARCHAR NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        );
        CREATE TABLE sar_drafts (
            sar_id VARCHAR PRIMARY KEY,
            narrative TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        );
        CREATE TABLE cases (
            case_id VARCHAR PRIMARY KEY,
            customer_id VARCHAR
        );
        CREATE TABLE case_feedback (
            id INTEGER PRIMARY KEY,
            case_id VARCHAR NOT NULL,
            analyst_decision VARCHAR NOT NULL,
            created_at DATETIME NOT NULL
        );
        INSERT INTO customers VALUES ('C1', 'Legacy', '2025-01-01', '2025-01-01');
        INSERT INTO transactions VALUES ('T1', 'A1', 'DEBIT', 12.34, '2025-01-01');
        INSERT INTO cases VALUES ('CASE1', 'C1');
        INSERT INTO case_feedback VALUES (1, 'CASE1', 'CONFIRMED', '2025-01-02');
        """
    )
    connection.commit()
    connection.close()

    engine = create_engine(f"sqlite:///{source}")
    assert migrate_database(engine) == SCHEMA_VERSION
    assert migrate_database(engine) == SCHEMA_VERSION

    with engine.connect() as migrated:
        assert migrated.execute(text("SELECT full_name FROM customers")).scalar_one() == "Legacy"
        assert migrated.execute(text("SELECT analyst_decision FROM case_feedback")).scalar_one() == "CONFIRMED"
        assert migrated.execute(text("SELECT amount_decimal FROM transactions")).scalar_one() == 12.34
        columns = {
            row[1]
            for row in migrated.execute(text("PRAGMA table_info(risk_assessments)"))
        }
        assert {"gnn_risk", "xgboost_risk", "final_risk", "risk_level"} <= columns
        assert migrated.execute(
            text("SELECT version FROM schema_migrations")
        ).scalar_one() == SCHEMA_VERSION
