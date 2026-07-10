from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.infrastructure.db.models import (
    CashFlowSource,
    ObjectStatus,
    ReportFormat,
    ReportType,
    ScenarioScope,
    ScenarioStatus,
    ScenarioType,
    UserRole,
)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


class ConstructionObjectCreate(BaseModel):
    name: str
    code: str
    construction_start: date
    construction_end: date
    status: ObjectStatus = ObjectStatus.planning

    @field_validator("construction_end")
    @classmethod
    def end_after_start(cls, v, info):
        start = info.data.get("construction_start")
        if start and v < start:
            raise ValueError("construction_end must be >= construction_start")
        return v


class ConstructionObjectResponse(ConstructionObjectCreate):
    id: UUID

    class Config:
        from_attributes = True


class ScenarioCreate(BaseModel):
    name: str
    type: ScenarioType
    scope: ScenarioScope
    construction_object_id: Optional[UUID] = None
    parent_version_id: Optional[UUID] = None

    @field_validator("construction_object_id")
    @classmethod
    def single_object_requires_id(cls, v, info):
        if info.data.get("scope") == ScenarioScope.single_object and not v:
            raise ValueError("construction_object_id required for single_object scope")
        return v


class ScenarioResponse(BaseModel):
    id: UUID
    name: str
    type: ScenarioType
    scope: ScenarioScope
    construction_object_id: Optional[UUID]
    version_number: int
    parent_version_id: Optional[UUID]
    status: ScenarioStatus
    calculated_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class CashFlowLineUpdate(BaseModel):
    base_amount: Optional[float] = None
    adjustment: Optional[float] = None


class CashFlowLineResponse(BaseModel):
    id: UUID
    scenario_id: UUID
    construction_object_id: UUID
    form_code: str
    line_item: str
    period: str
    base_amount: float
    adjustment: Optional[float]
    consensus_amount: float
    actual_amount: Optional[float]
    source: CashFlowSource

    class Config:
        from_attributes = True


class AdjustmentRequest(BaseModel):
    form_code: str
    period: str
    total_adjustment: float
    construction_object_id: Optional[UUID] = None


class FinancialResultResponse(BaseModel):
    period: str
    revenue: float
    costs: float
    profit: float
    is_consolidated: bool = False
    construction_object_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class ReportGenerateRequest(BaseModel):
    scenario_id: UUID
    type: ReportType
    format: ReportFormat
    construction_object_id: Optional[UUID] = None


class ReportResponse(BaseModel):
    id: UUID
    scenario_id: UUID
    format: ReportFormat
    type: ReportType
    generated_at: datetime
    file_path: str

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    role: UserRole
    construction_object_id: Optional[UUID] = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: UserRole
    construction_object_id: Optional[UUID]

    class Config:
        from_attributes = True
