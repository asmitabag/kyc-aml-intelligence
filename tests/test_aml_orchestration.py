from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from services.aml_runtime import AMLRuntimeOrchestrator
from services.cases import models
from services.model_adapters.contracts import InferenceResult, ModelStatus
from shared.schemas.aml import AMLResponse


def make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    models.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


class AvailableGNN:
    def analyze(self, graph):
        assert graph.contract_version == "aml-runtime.v1"
        assert graph.edges[0].timestamp == datetime(2024, 1, 1)
        return InferenceResult(
            model_name="gnn",
            status=ModelStatus.AVAILABLE,
            score=0.9,
            model_version="test-gnn",
            output=AMLResponse(
                case_id="runtime",
                aml_risk=0.9,
                suspected_typology="structuring",
                suspicious_transaction_ids=[graph.edges[0].transaction_id],
                suspicious_account_ids=[graph.edges[0].source_account_id],
                explanation_subgraph={},
                graph_features=graph.numeric_features,
            ),
        )


class UnavailableXGBoost:
    def predict(self, features):
        return InferenceResult(
            model_name="xgboost",
            status=ModelStatus.UNAVAILABLE,
            error="test artifact unavailable",
        )


def seed_customer(db):
    db.add(models.Customer(customer_id="C1", full_name="Customer"))
    db.add(models.Account(account_id="A1", customer_id="C1"))
    db.add(
        models.Transaction(
            transaction_id="T1",
            account_id="A1",
            direction="DEBIT",
            amount=100,
            currency="USD",
            occurred_at=datetime(2024, 1, 1),
        )
    )
    db.add(
        models.KYCResult(
            kyc_id="K1",
            customer_id="C1",
            document_tamper_probability=0.1,
            liveness_probability=0.1,
            deepfake_probability=0.1,
            kyc_risk=0.5,
            document_fingerprint="fingerprint",
            model_version="test-kyc",
        )
    )
    db.commit()


def test_successful_runtime_persists_assessment_and_boundary_alert():
    db = make_db()
    seed_customer(db)
    result = AMLRuntimeOrchestrator(
        AvailableGNN(), alert_threshold=0.715
    ).analyze(db, "C1")

    assert result.status == "completed"
    assert result.fused_risk == 0.9
    assert result.alert_id is not None
    assessment = db.query(models.RiskAssessment).one()
    alert = db.query(models.Alert).one()
    assert assessment.gnn_risk == 0.9
    assert assessment.xgboost_risk is None
    assert assessment.xgboost_model_version is None
    assert assessment.final_risk == 0.9
    assert assessment.risk_level == "HIGH"
    assert assessment.gnn_model_version == "test-gnn"
    assert alert.assessment is assessment
    assert alert.reason_code == "AML_RISK_THRESHOLD"
    db.close()


def test_unavailable_models_do_not_persist_assessment():
    db = make_db()
    seed_customer(db)
    result = AMLRuntimeOrchestrator().analyze(db, "C1")

    assert result.status == "unavailable"
    assert result.assessment_id is None
    assert db.query(models.RiskAssessment).count() == 0
    assert db.query(models.Alert).count() == 0
    db.close()


def test_xgboost_unavailable_does_not_block_gnn_only_analysis():
    db = make_db()
    seed_customer(db)
    result = AMLRuntimeOrchestrator(
        AvailableGNN(),
        UnavailableXGBoost(),
    ).analyze(db, "C1")

    assert result.status == "completed"
    assert result.fused_risk == 0.9
    assert result.model_statuses["gnn"] == "available"
    assert result.model_statuses["xgboost"] == "disabled"
    assessment = db.query(models.RiskAssessment).one()
    assert assessment.gnn_risk == 0.9
    assert assessment.final_risk == 0.9
    assert assessment.xgboost_risk is None
    assert assessment.xgboost_model_version is None
    db.close()


def test_missing_customer_and_empty_history_are_structured_inputs():
    db = make_db()
    assert AMLRuntimeOrchestrator().analyze(db, "missing").status == "not_found"
    db.add(models.Customer(customer_id="EMPTY", full_name="Empty"))
    db.commit()
    assert AMLRuntimeOrchestrator().analyze(db, "EMPTY").status == "invalid_input"
    db.close()