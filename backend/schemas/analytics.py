from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class MetricsResponse(BaseModel):
    total: int
    pending: int
    acknowledged: int
    in_consultation: int
    completed: int
    back_referrals: int
    followups_due: int
    overdue_followups: int
    avg_ack_hours: float
    completion_rate_pct: float
    facility_workloads: List[Dict[str, Any]]
    monthly_trends: List[Dict[str, Any]]
