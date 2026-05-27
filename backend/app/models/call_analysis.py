import uuid
import json
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class CallAnalysis(Base):
    __tablename__ = "call_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    manager_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("managers.id"), nullable=False)
    crm_item_id: Mapped[str] = mapped_column(String(100), nullable=True)   # dedup key
    item_type: Mapped[str] = mapped_column(String(20), nullable=False, default="call")  # call | chat
    item_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)

    transcript: Mapped[str] = mapped_column(Text, nullable=True)

    # 6 competency scores 0-10
    score_greeting: Mapped[float] = mapped_column(Float, default=0.0)
    score_needs: Mapped[float] = mapped_column(Float, default=0.0)
    score_presentation: Mapped[float] = mapped_column(Float, default=0.0)
    score_objections: Mapped[float] = mapped_column(Float, default=0.0)
    score_closing: Mapped[float] = mapped_column(Float, default=0.0)
    score_next_step: Mapped[float] = mapped_column(Float, default=0.0)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)

    strengths: Mapped[str] = mapped_column(Text, nullable=True)    # JSON array
    improvements: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    verdict: Mapped[str] = mapped_column(String(20), nullable=True)  # strong|average|weak

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    manager = relationship("Manager", back_populates="call_analyses")
