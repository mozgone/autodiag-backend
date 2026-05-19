from pydantic import BaseModel
from typing import List, Optional

class OverviewStats(BaseModel):
    total_managers: int
    active_deals: int
    total_revenue_month: float
    avg_conversion_rate: float
    plan_completion_avg: float
    top_performer: Optional[str]
    at_risk_deals: int

class FunnelStage(BaseModel):
    stage: str
    count: int
    amount: float
    avg_days: float

class ChartPoint(BaseModel):
    date: str
    value: float
    label: Optional[str] = None

class ManagerRanking(BaseModel):
    rank: int
    manager_id: str
    full_name: str
    revenue: float
    plan_completion: float
    calls_count: int
    trend: str
