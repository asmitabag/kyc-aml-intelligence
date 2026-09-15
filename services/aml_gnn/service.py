from shared.schemas.aml import AMLResponse


def run_aml_analysis(case_id: str) -> AMLResponse:
    return AMLResponse(
        case_id=case_id,
        aml_risk=0.91,
        suspected_typology="layering",
        suspicious_transaction_ids=["T001"],
        suspicious_account_ids=["A001"],
        explanation_subgraph={
            "nodes": ["A001", "A002"],
            "edges": [
                {
                    "source": "A001",
                    "target": "A002",
                    "transaction_id": "T001",
                    "importance": 0.87
                }
            ],
            "important_features": [
                {
                    "feature": "transaction_amount",
                    "importance": 0.91
                },
                {
                    "feature": "transaction_frequency",
                    "importance": 0.76
                }
            ]
        },
        graph_features={"degree": 12}
    )