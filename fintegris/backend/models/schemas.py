from pydantic import BaseModel
from typing import Optional


class ReviewDecision(BaseModel):
    decision: str  # "Approved" | "Rejected" | "Investigating"
    decided_by: Optional[str] = "Reviewer"
    notes: Optional[str] = None
