from apps.api_gateway.database import SessionLocal, Base, engine
from services.aml_gnn.service import run_aml_analysis
from services.xai.triage import create_triage
from services.cases.service import create_case, update_case_status
from shared.schemas.kyc import KYCResponse


DEMO_CASES = [
    {
        "customer_id": "CUST002",
        "document_tamper_probability": 0.05,
        "liveness_probability": 0.97,
        "deepfake_probability": 0.02,
        "kyc_risk": 0.20,
        "document_fingerprint": "DOC-FP-002",
        "tamper_mask_path": "data/evidence/CUST002_tamper_mask.png",
        "evidence_ids": ["DOC002", "FACE002"],
        "status": "CLOSED",
    },
    {
        "customer_id": "CUST003",
        "document_tamper_probability": 0.15,
        "liveness_probability": 0.92,
        "deepfake_probability": 0.05,
        "kyc_risk": 0.45,
        "document_fingerprint": "DOC-FP-003",
        "tamper_mask_path": "data/evidence/CUST003_tamper_mask.png",
        "evidence_ids": ["DOC003", "FACE003"],
        "status": "OPEN",
    },
    {
        "customer_id": "CUST004",
        "document_tamper_probability": 0.35,
        "liveness_probability": 0.78,
        "deepfake_probability": 0.20,
        "kyc_risk": 0.70,
        "document_fingerprint": "DOC-FP-004",
        "tamper_mask_path": "data/evidence/CUST004_tamper_mask.png",
        "evidence_ids": ["DOC004", "FACE004", "TAMPER004"],
        "status": "UNDER_REVIEW",
    },
    {
        "customer_id": "CUST005",
        "document_tamper_probability": 0.65,
        "liveness_probability": 0.55,
        "deepfake_probability": 0.40,
        "kyc_risk": 0.90,
        "document_fingerprint": "DOC-FP-005",
        "tamper_mask_path": "data/evidence/CUST005_tamper_mask.png",
        "evidence_ids": ["DOC005", "FACE005", "TAMPER005"],
        "status": "UNDER_REVIEW",
    },
    {
        "customer_id": "CUST006",
        "document_tamper_probability": 0.01,
        "liveness_probability": 0.99,
        "deepfake_probability": 0.01,
        "kyc_risk": 0.05,
        "document_fingerprint": "DOC-FP-006",
        "tamper_mask_path": "data/evidence/CUST006_tamper_mask.png",
        "evidence_ids": ["DOC006", "FACE006"],
        "status": "OPEN",
    },
]


def seed_demo_cases():
    # Make sure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        for data in DEMO_CASES:

            customer_id = data["customer_id"]

            # Avoid duplicate cases if script is run twice
            existing_case = next(
                (case for case in db.query(
                    __import__(
                        "services.cases.models",
                        fromlist=["Case"]
                    ).Case
                ).filter_by(customer_id=customer_id).all()),
                None,
            )

            if existing_case:
                print(f"Skipping {customer_id} - already exists")
                continue

            # Build KYC response using existing schema
            kyc = KYCResponse(
                customer_id=customer_id,
                document_tamper_probability=data["document_tamper_probability"],
                liveness_probability=data["liveness_probability"],
                deepfake_probability=data["deepfake_probability"],
                kyc_risk=data["kyc_risk"],
                document_fingerprint=data["document_fingerprint"],
                tamper_mask_path=data["tamper_mask_path"],
                evidence_ids=data["evidence_ids"],
            )

            # Use the EXISTING AML service
            aml = run_aml_analysis(customer_id)

            # Use the EXISTING triage implementation
            triage = create_triage(kyc, aml)

            # Use the EXISTING case creation service
            case = create_case(
                db=db,
                kyc=kyc,
                aml=aml,
                triage=triage,
            )

            # Apply desired demo status
            if data["status"] != "OPEN":
                case = update_case_status(
                    db,
                    case.case_id,
                    data["status"],
                )

            print(
                f"Created {customer_id} | "
                f"Case={case.case_id} | "
                f"Risk={case.fused_risk} | "
                f"Priority={case.priority} | "
                f"Status={case.status}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_cases()