from shared.schemas.aml import AMLResponse


def run_aml_analysis(case_id: str) -> AMLResponse:
    """
    Temporary mock AML service.

    This will later be replaced by the actual AML GNN pipeline.
    The output contract must remain AMLResponse.
    """

    return AMLResponse(
        case_id=case_id,
        aml_risk=0.91,
        suspected_typology="layering",
        suspicious_transaction_ids=["T001"],
        suspicious_account_ids=["A001"],
        explanation_subgraph={
            "nodes": ["A001", "A002"]
        },
        graph_features={
            "degree": 12
        }
    )