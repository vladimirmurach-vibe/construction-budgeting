import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.session import Base


class ObjectStatus(str, enum.Enum):
    planning = "planning"
    in_progress = "in_progress"
    completed = "completed"
    suspended = "suspended"


class ScenarioType(str, enum.Enum):
    budget = "budget"
    forecast = "forecast"


class ScenarioScope(str, enum.Enum):
    all_objects = "all_objects"
    single_object = "single_object"


class ScenarioStatus(str, enum.Enum):
    draft = "draft"
    calculated = "calculated"
    approved = "approved"
    archived = "archived"


class CashFlowSource(str, enum.Enum):
    manual = "manual"
    import_ = "import"
    accounting_system = "accounting_system"


class UserRole(str, enum.Enum):
    admin = "admin"
    management = "management"
    governance = "governance"
    budget_analyst = "budget_analyst"
    project_manager = "project_manager"


class ReportFormat(str, enum.Enum):
    pdf = "pdf"
    excel = "excel"


class ReportType(str, enum.Enum):
    consolidated = "consolidated"
    by_object = "by_object"
    comparison = "comparison"


class ConstructionObject(Base):
    __tablename__ = "construction_objects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    construction_start: Mapped[datetime] = mapped_column(Date, nullable=False)
    construction_end: Mapped[datetime] = mapped_column(Date, nullable=False)
    status: Mapped[ObjectStatus] = mapped_column(Enum(ObjectStatus), nullable=False, default=ObjectStatus.planning)

    scenarios: Mapped[list["Scenario"]] = relationship(back_populates="construction_object")
    cash_flow_lines: Mapped[list["CashFlowLine"]] = relationship(back_populates="construction_object")


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[ScenarioType] = mapped_column(Enum(ScenarioType), nullable=False)
    scope: Mapped[ScenarioScope] = mapped_column(Enum(ScenarioScope), nullable=False)
    construction_object_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("construction_objects.id"), nullable=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id"), nullable=True
    )
    status: Mapped[ScenarioStatus] = mapped_column(Enum(ScenarioStatus), nullable=False, default=ScenarioStatus.draft)
    calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    construction_object: Mapped["ConstructionObject | None"] = relationship(back_populates="scenarios")
    cash_flow_lines: Mapped[list["CashFlowLine"]] = relationship(back_populates="scenario")
    financial_results: Mapped[list["FinancialResult"]] = relationship(back_populates="scenario")
    reports: Mapped[list["Report"]] = relationship(back_populates="scenario")


class InputForm(Base):
    __tablename__ = "input_forms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    object_bound: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class CashFlowLine(Base):
    __tablename__ = "cash_flow_lines"
    __table_args__ = (
        UniqueConstraint(
            "scenario_id", "construction_object_id", "form_code", "line_item", "period",
            name="uq_cash_flow_line",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scenarios.id"), nullable=False)
    construction_object_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("construction_objects.id"), nullable=False
    )
    form_code: Mapped[str] = mapped_column(String(64), nullable=False)
    line_item: Mapped[str] = mapped_column(String(128), nullable=False)
    period: Mapped[str] = mapped_column(String(7), nullable=False)
    base_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    adjustment: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True, default=0)
    consensus_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    actual_amount: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    source: Mapped[CashFlowSource] = mapped_column(
        Enum(CashFlowSource), nullable=False, default=CashFlowSource.manual
    )

    scenario: Mapped["Scenario"] = relationship(back_populates="cash_flow_lines")
    construction_object: Mapped["ConstructionObject"] = relationship(back_populates="cash_flow_lines")


class FinancialResult(Base):
    __tablename__ = "financial_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scenarios.id"), nullable=False)
    construction_object_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("construction_objects.id"), nullable=True
    )
    period: Mapped[str] = mapped_column(String(7), nullable=False)
    revenue: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    costs: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    profit: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    is_consolidated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    scenario: Mapped["Scenario"] = relationship(back_populates="financial_results")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    construction_object_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("construction_objects.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scenarios.id"), nullable=False)
    format: Mapped[ReportFormat] = mapped_column(Enum(ReportFormat), nullable=False)
    type: Mapped[ReportType] = mapped_column(Enum(ReportType), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)

    scenario: Mapped["Scenario"] = relationship(back_populates="reports")


class FactLoadLog(Base):
    __tablename__ = "fact_load_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    records_loaded: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
