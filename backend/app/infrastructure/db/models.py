from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.session import Base


class ConstructionObject(Base):
    __tablename__ = "construction_objects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    construction_start: Mapped[date] = mapped_column(Date, nullable=False)
    construction_end: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="in_progress", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    scenarios: Mapped[list["Scenario"]] = relationship(back_populates="construction_object")


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    construction_object_id: Mapped[int | None] = mapped_column(
        ForeignKey("construction_objects.id"), nullable=True
    )
    version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    parent_version_id: Mapped[int | None] = mapped_column(ForeignKey("scenarios.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    calculated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    construction_object: Mapped[ConstructionObject | None] = relationship(back_populates="scenarios")
    parent_version: Mapped["Scenario | None"] = relationship(remote_side=[id])
    cash_flow_lines: Mapped[list["CashFlowLine"]] = relationship(
        back_populates="scenario", cascade="all, delete-orphan"
    )
    financial_results: Mapped[list["FinancialResult"]] = relationship(
        back_populates="scenario", cascade="all, delete-orphan"
    )


class CashFlowLine(Base):
    __tablename__ = "cash_flow_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id"), nullable=False, index=True)
    construction_object_id: Mapped[int] = mapped_column(
        ForeignKey("construction_objects.id"), nullable=False, index=True
    )
    form_code: Mapped[str] = mapped_column(String(64), nullable=False)
    line_item: Mapped[str] = mapped_column(String(255), nullable=False)
    period: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    base_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    adjustment: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    consensus_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    actual_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="manual", nullable=False)

    scenario: Mapped[Scenario] = relationship(back_populates="cash_flow_lines")
    construction_object: Mapped[ConstructionObject] = relationship()


class FinancialResult(Base):
    __tablename__ = "financial_results"
    __table_args__ = (
        UniqueConstraint(
            "scenario_id",
            "construction_object_id",
            "period",
            "is_consolidated",
            name="uq_financial_result_period",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id"), nullable=False, index=True)
    construction_object_id: Mapped[int | None] = mapped_column(
        ForeignKey("construction_objects.id"), nullable=True, index=True
    )
    period: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    revenue: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    costs: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    profit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_consolidated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    scenario: Mapped[Scenario] = relationship(back_populates="financial_results")
    construction_object: Mapped[ConstructionObject | None] = relationship()


class InputForm(Base):
    __tablename__ = "input_forms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    format: Mapped[str] = mapped_column(String(16), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class FactLoadLog(Base):
    __tablename__ = "fact_load_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    records_loaded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
