from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ManagerBase(BaseModel):
    full_name: str
    email: Optional[str] = None
    monthly_plan: float = 0.0

class ManagerCreate(ManagerBase):
    team_id: Optional[str] = None

class ManagerStats(BaseModel):
    calls_count: int = 0
    calls_quality_avg: float = 0.0
    deals_created: int = 0
    deals_won: int = 0
    conversion_rate: float = 0.0
    revenue: float = 0.0
    plan_completion: float = 0.0
    crm_fill_rate: float = 0.0
    overdue_tasks: int = 0
    trend: str = "stable"  # up, down, stable

class RecommendationOut(BaseModel):
    id: str
    rec_type: str
    title: str
    content: str
    priority: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ManagerOut(BaseModel):
    id: str
    full_name: str
    email: Optional[str]
    team_id: Optional[str]
    monthly_plan: float
    is_active: bool
    stats: Optional[ManagerStats] = None
    avatar_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ManagerDetail(ManagerOut):
    recommendations: List[RecommendationOut] = []
    weekly_history: List[dict] = []
