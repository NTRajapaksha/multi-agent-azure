from pydantic import BaseModel, Field
from typing import Optional

class CustomerProfile(BaseModel):
    tenure_months: int
    monthly_bill: float
    service_type: str

class RiskAssessment(BaseModel):
    score: int = Field(ge=0, le=100)
    reasoning: str
    confidence: str = Field(pattern="^(high|medium|low)$")

class AgentState(BaseModel):
    customer_id: str
    customer_profile: Optional[CustomerProfile] = None
    complaint_context: Optional[str] = None
    risk_assessment: Optional[RiskAssessment] = None
    recommended_offer: Optional[str] = None
    requires_human_approval: bool = False
    retry_count: int = 0
    error: Optional[str] = None
