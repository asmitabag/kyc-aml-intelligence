from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    JSON
)
from sqlalchemy.orm import relationship

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

    feedback = relationship(
        "CaseFeedback",
        back_populates="case",
        cascade="all, delete-orphan"
    )

class CaseFeedback(Base):
    __tablename__ = "case_feedback"

    id = Column(Integer, primary_key=True, index=True)

    case_id = Column(
        String,
        ForeignKey("cases.case_id"),
        nullable=False
    )

    analyst_decision = Column(String, nullable=False)

    comment = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    case = relationship("Case", back_populates="feedback")