
from datetime import datetime

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TransactionAMLRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    Timestamp: datetime
    Amount_Received: float = Field(ge=0, alias="Amount Received")
    Amount_Paid: float = Field(ge=0, alias="Amount Paid")
    Receiving_Currency: str = Field(alias="Receiving Currency")
    Payment_Currency: str = Field(alias="Payment Currency")
    Account: str
    Account_1: str = Field(alias="Account.1")
    From_Bank: str = Field(alias="From Bank")
    To_Bank: str = Field(alias="To Bank")
    Payment_Format: str = Field(alias="Payment Format")

    def to_model_row(self) -> dict:
        return {
            "Timestamp": self.Timestamp,
            "Amount Received": self.Amount_Received,
            "Amount Paid": self.Amount_Paid,
            "Receiving Currency": self.Receiving_Currency,
            "Payment Currency": self.Payment_Currency,
            "Account": self.Account,
            "Account.1": self.Account_1,
            "From Bank": self.From_Bank,
            "To Bank": self.To_Bank,
            "Payment Format": self.Payment_Format,
        }


class TransactionAMLResponse(BaseModel):
    model_name: str
    model_version: Optional[str] = None
    status: str
    ranking_score: Optional[float] = None
    feature_count: Optional[int] = None
    interpretation: Optional[str] = None
    error: Optional[str] = None
