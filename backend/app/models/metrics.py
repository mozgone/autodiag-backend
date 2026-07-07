import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Float, Integer, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class MetricSnapshot(Base):
    """Ежедневный/еженедельный снимок метрик менеджера."""
    __tablename__ = "metric_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    manager_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("managers.id"), nullable=False)
    period_type: Mapped[str] = mapped_column(String(20), default="daily")  # daily, weekly, monthly
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Звонки
    calls_count: Mapped[int] = mapped_column(Integer, default=0)
    calls_duration_avg: Mapped[float] = mapped_column(Float, default=0.0)  # seconds
    calls_quality_avg: Mapped[float] = mapped_column(Float, default=0.0)  # 0-10

    # Сделки
    deals_created: Mapped[int] = mapped_column(Integer, default=0)
    deals_won: Mapped[int] = mapped_column(Integer, default=0)
    deals_lost: Mapped[int] = mapped_column(Integer, default=0)
    conversion_rate: Mapped[float] = mapped_column(Float, default=0.0)  # %
    avg_deal_size: Mapped[float] = mapped_column(Float, default=0.0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)

    # Качество CRM
    crm_fill_rate: Mapped[float] = mapped_column(Float, default=0.0)  # % заполненных полей
    overdue_tasks: Mapped[int] = mapped_column(Integer, default=0)
    activities_count: Mapped[int] = mapped_column(Integer, default=0)

    # Прогноз
    plan_completion_forecast: Mapped[float] = mapped_column(Float, default=0.0)  # %

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    manager = relationship("Manager", back_populates="metric_snapshots")

class Recommendation(Base):
    """ИИ-рекомендация для менеджера."""
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    manager_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("managers.id"), nullable=False)
    rec_type: Mapped[str] = mapped_column(String(50), nullable=False)  # strength, growth, alert, forecast
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1)  # 1=low, 2=medium, 3=high
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    manager = relationship("Manager", back_populates="recommendations")
