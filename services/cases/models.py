from sqlalchemy import Column, String, Float, Boolean, JSON
from apps.api_gateway.database import Base


class Case(Base):
    __tablename__ = "cases"

    case_id = Column(String, primary_key=True, index=True)

    customer_id = Column(String, nullable=True)

    kyc_risk = Column(Float, nullable=True)
    aml_risk = Column(Float, nullable=True)
    fused_risk = Column(Float, nullable=True)

    uncertainty = Column(Float, nullable=True)

    priority = Column(String, nullable=True)

    human_review_required = Column(Boolean, default=False)

    suspected_typology = Column(String, nullable=True)

    shap_features = Column(JSON, nullable=True)
    graph_explanation = Column(JSON, nullable=True)

    status = Column(String, default="OPEN")