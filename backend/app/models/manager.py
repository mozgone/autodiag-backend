import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    monthly_plan: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="teams")
    managers = relationship("Manager", back_populates="team")

class Manager(Base):
    __tablename__ = "managers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    crm_id: Mapped[str] = mapped_column(String(100), nullable=True)  # ID в CRM
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=True)
    monthly_plan: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="managers")
    team = relationship("Team", back_populates="managers")
    deals = relationship("Deal", back_populates="manager", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="manager", cascade="all, delete-orphan")
    metric_snapshots = relationship("MetricSnapshot", back_populates="manager", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="manager", cascade="all, delete-orphan")
