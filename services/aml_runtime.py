from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from services.cases import models
from services.cases.service import create_alert, create_risk_assessment
from services.model_adapters.contracts import InferenceResult, ModelStatus
from services.model_adapters.gnn import GNNAdapter, UnavailableGNNAdapter
from services.model_adapters.risk import RiskComponent, fuse_available_scores
from services.model_adapters.runtime import (
    GNNRuntimeInput,
    GraphEdge,
    GraphNode,
    RUNTIME_CONTRACT_VERSION,
    XGBoostRuntimeInput,
    build_xgboost_features,
)
from services.model_adapters.xgboost import (
    UnavailableXGBoostAdapter,
    XGBoostAdapter,
)
from services.gemini_aml_fallback import GeminiAMLExplanationFallback


ALERT_THRESHOLD = 0.8


@dataclass(frozen=True)
class AMLAnalysisResult:
    status: str
    customer_id: str
    message: str
    assessment_id: Optional[str] = None
    alert_id: Optional[str] = None
    fused_risk: Optional[float] = None
    model_statuses: Optional[dict[str, str]] = None
    model_versions: Optional[dict[str, Optional[str]]] = None
    explanations: Optional[dict[str, Any]] = None


class AMLRuntimeOrchestrator:
    def __init__(
        self,
        gnn_adapter: Optional[GNNAdapter] = None,
        xgboost_adapter: Optional[XGBoostAdapter] = None,
        alert_threshold: float = ALERT_THRESHOLD,
    ) -> None:
        if not 0.0 <= alert_threshold <= 1.0:
            raise ValueError("Alert threshold must be between 0 and 1")
        self.gnn_adapter = gnn_adapter or UnavailableGNNAdapter()
        self.xgboost_adapter = xgboost_adapter or UnavailableXGBoostAdapter()
        self.alert_threshold = alert_threshold
        self.gemini_fallback = GeminiAMLExplanationFallback()

    def analyze(self, db: Session, customer_id: str) -> AMLAnalysisResult:
        customer = (
            db.query(models.Customer)
            .filter(models.Customer.customer_id == customer_id)
            .first()
        )
        if customer is None:
            return AMLAnalysisResult(
                status="not_found",
                customer_id=customer_id,
                message="Customer not found",
            )

        accounts = (
            db.query(models.Account)
            .filter(models.Account.customer_id == customer_id)
            .all()
        )
        account_ids = {account.account_id for account in accounts}
        transactions = (
            db.query(models.Transaction)
            .filter(models.Transaction.account_id.in_(account_ids))
            .order_by(models.Transaction.occurred_at.asc())
            .all()
            if account_ids
            else []
        )
        if not transactions:
            return AMLAnalysisResult(
                status="invalid_input",
                customer_id=customer_id,
                message="Customer has no persisted transaction history",
            )

        account_lookup = {
            account.account_id: account for account in db.query(models.Account).all()
        }
        for transaction in transactions:
            if transaction.account_id not in account_ids:
                return AMLAnalysisResult(
                    status="invalid_input",
                    customer_id=customer_id,
                    message="Transaction source account is not owned by customer",
                )
            if (
                transaction.to_account_id is not None
                and transaction.to_account_id not in account_lookup
            ):
                return AMLAnalysisResult(
                    status="invalid_input",
                    customer_id=customer_id,
                    message="Transaction recipient account does not exist",
                )

        graph = self._build_graph(
            customer_id,
            account_ids,
            transactions,
            accounts=accounts,
        )
        kyc = (
            db.query(models.KYCResult)
            .filter(models.KYCResult.customer_id == customer_id)
            .order_by(models.KYCResult.created_at.desc())
            .first()
        )
        if kyc is None:
            return AMLAnalysisResult(
                status="invalid_input",
                customer_id=customer_id,
                message="Customer has no persisted KYC result",
            )

        gnn_result = self.gnn_adapter.analyze(graph)
        statuses = {
            gnn_result.model_name: gnn_result.status.value,
            "xgboost": "disabled",
        }
        versions = {
            gnn_result.model_name: gnn_result.model_version,
            "xgboost": None,
        }
        if gnn_result.status is not ModelStatus.AVAILABLE:
            return AMLAnalysisResult(
                status="unavailable",
                customer_id=customer_id,
                message=(
                    "GNN model is unavailable: "
                    f"{gnn_result.error or gnn_result.status.value}"
                ),
                model_statuses=statuses,
                model_versions=versions,
            )
        self._validate_result(gnn_result)
        # Experimental GNN-only score; KYC is required but not blended.
        fusion = gnn_result.score

        gnn_score = gnn_result.score
        assessment_id = f"ASM-{uuid4().hex[:12].upper()}"
        assessment = create_risk_assessment(
            db=db,
            assessment_id=assessment_id,
            customer_id=customer_id,
            kyc_risk=kyc.kyc_risk,
            aml_risk=gnn_score,
            fused_risk=fusion,
            priority="HIGH" if fusion >= self.alert_threshold else "MEDIUM",
            human_review_required=fusion >= self.alert_threshold,
            suspected_typology=(
                gnn_result.output.suspected_typology
                if gnn_result.output is not None
                else None
            ),
            gnn_risk=gnn_result.score,
            xgboost_risk=None,
            final_risk=fusion,
            risk_level="HIGH" if fusion >= self.alert_threshold else "MEDIUM",
            gnn_model_version=gnn_result.model_version,
            xgboost_model_version=None,
        )
        alert_id = None
        if fusion >= self.alert_threshold:
            alert_id = f"ALT-{uuid4().hex[:12].upper()}"
            create_alert(
                db=db,
                alert_id=alert_id,
                customer_id=customer_id,
                alert_type="AML_RISK_THRESHOLD",
                severity="HIGH",
                assessment_id=assessment.assessment_id,
                reason_code="AML_RISK_THRESHOLD",
                narrative="Risk assessment reached the configured alert threshold",
            )

        explanations = {}
        if gnn_result.explanation is not None:
            explanations["gnn"] = gnn_result.explanation

        if not explanations:
            fallback_explanation = self.gemini_fallback.explain({
                "customer_id": customer_id,
                "kyc_risk": kyc.kyc_risk,
                "gnn_score": gnn_result.score,
                "fused_risk": fusion,
                "suspected_typology": (
                    gnn_result.output.suspected_typology
                    if gnn_result.output is not None
                    else None
                ),
                "transaction_count": len(transactions),
                "account_count": len(accounts),
            })
            if fallback_explanation:
                explanations["gemini_fallback"] = fallback_explanation
        return AMLAnalysisResult(
            status="completed",
            customer_id=customer_id,
            message="AML analysis completed",
            assessment_id=assessment.assessment_id,
            alert_id=alert_id,
            fused_risk=fusion,
            model_statuses={**statuses, "kyc": ModelStatus.AVAILABLE.value},
            model_versions={**versions, "kyc": kyc.model_version},
            explanations=explanations,
        )

    @staticmethod
    def _validate_result(result: InferenceResult[Any]) -> None:
        if result.score is None or not 0.0 <= result.score <= 1.0:
            raise ValueError(f"{result.model_name} returned an invalid score")

    @staticmethod
    def _build_graph(
        customer_id: str,
        account_ids: set[str],
        transactions: list[models.Transaction],
        accounts: Optional[list[models.Account]] = None,
    ) -> GNNRuntimeInput:
        account_lookup = {
            account.account_id: account
            for account in (accounts or [])
        }

        nodes = [
            *(
                GraphNode(
                    node_id=account_id,
                    node_type="account",
                    account_type=(
                        account_lookup[account_id].account_type
                        if account_id in account_lookup
                        else None
                    ),
                    currency=(
                        account_lookup[account_id].currency
                        if account_id in account_lookup
                        else None
                    ),
                )
                for account_id in sorted(account_ids)
            ),
            *(
                GraphNode(transaction.transaction_id, "transaction")
                for transaction in transactions
            ),
        ]

        edges = tuple(
            GraphEdge(
                transaction_id=transaction.transaction_id,
                source_account_id=transaction.account_id,
                target_account_id=transaction.to_account_id,
                amount=float(transaction.amount),
                currency=transaction.currency,
                timestamp=transaction.occurred_at,
            )
            for transaction in transactions
        )

        total_amount = sum(float(t.amount) for t in transactions)

        return GNNRuntimeInput(
            contract_version=RUNTIME_CONTRACT_VERSION,
            customer_id=customer_id,
            nodes=tuple(nodes),
            edges=edges,
            numeric_features={
                "account_count": float(len(account_ids)),
                "transaction_count": float(len(transactions)),
                "total_amount": total_amount,
            },
        )

    @staticmethod
    def _build_xgboost_input(
        customer_id: str,
        accounts: list[models.Account],
        transactions: list[models.Transaction],
    ) -> XGBoostRuntimeInput:
        amounts = [float(transaction.amount) for transaction in transactions]
        debit_total = sum(
            amount
            for amount, transaction in zip(amounts, transactions)
            if transaction.direction == "DEBIT"
        )
        credit_total = sum(
            amount
            for amount, transaction in zip(amounts, transactions)
            if transaction.direction == "CREDIT"
        )
        features = build_xgboost_features(
            account_count=len(accounts),
            transaction_count=len(transactions),
            debit_total=debit_total,
            credit_total=credit_total,
            mean_amount=sum(amounts) / len(amounts),
            max_amount=max(amounts),
            distinct_counterparties=len({
                transaction.counterparty
                for transaction in transactions
                if transaction.counterparty
            }),
        )
        return XGBoostRuntimeInput(
            contract_version=RUNTIME_CONTRACT_VERSION,
            customer_id=customer_id,
            numeric_features=features,
        )