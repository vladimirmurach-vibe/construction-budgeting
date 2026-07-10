from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


ScenarioType = Literal["budget", "forecast"]
ScenarioScope = Literal["all_objects", "single_object"]
ScenarioStatus = Literal["draft", "calculated", "approved", "archived"]
LineSource = Literal["manual", "import", "accounting_system"]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


class UserBase(BaseModel):
    email: str
    role: str
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(min_length=1)


class UserUpdate(BaseModel):
    email: str | None = None
    role: str | None = None
    is_active: bool | None = None
    password: str | None = None


class UserRead(UserBase):
    id: int
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ConstructionObjectBase(BaseModel):
    name: str
    code: str
    construction_start: date
    construction_end: date
    status: str = "in_progress"

    @model_validator(mode="after")
    def validate_dates(self):
        if self.construction_end < self.construction_start:
            raise ValueError("construction_end must be greater than or equal to construction_start")
        return self


class ConstructionObjectCreate(ConstructionObjectBase):
    pass


class ConstructionObjectUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    construction_start: date | None = None
    construction_end: date | None = None
    status: str | None = None


class ConstructionObjectRead(ConstructionObjectBase):
    id: int
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ScenarioCreate(BaseModel):
    name: str
    type: ScenarioType
    scope: ScenarioScope
    construction_object_id: int | None = None
    parent_version_id: int | None = None

    @model_validator(mode="after")
    def validate_scope(self):
        if self.scope == "single_object" and self.construction_object_id is None:
            raise ValueError("single_object scenarios require construction_object_id")
        return self


class ScenarioUpdate(BaseModel):
    name: str | None = None
    type: ScenarioType | None = None
    scope: ScenarioScope | None = None
    construction_object_id: int | None = None
    status: ScenarioStatus | None = None


class ScenarioRead(BaseModel):
    id: int
    name: str
    type: str
    scope: str
    construction_object_id: int | None = None
    version_number: int
    parent_version_id: int | None = None
    status: str
    calculated_at: datetime | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CashFlowLineRead(BaseModel):
    id: int
    scenario_id: int
    construction_object_id: int
    form_code: str
    line_item: str
    period: str
    base_amount: float
    adjustment: float
    consensus_amount: float
    actual_amount: float | None = None
    source: str

    model_config = ConfigDict(from_attributes=True)


class CashFlowLineUpdate(BaseModel):
    base_amount: float | None = None
    adjustment: float | None = None


class FinancialResultRead(BaseModel):
    id: int
    scenario_id: int
    construction_object_id: int | None = None
    period: str
    revenue: float
    costs: float
    profit: float
    is_consolidated: bool

    model_config = ConfigDict(from_attributes=True)


class ReportGenerateRequest(BaseModel):
    scenario_id: int
    type: str
    format: Literal["excel", "pdf"]


class ReportRead(BaseModel):
    id: int
    scenario_id: int
    type: str
    format: str
    file_path: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ImportValidateRequest(BaseModel):
    file_path: str


class ImportRequest(BaseModel):
    scenario_id: int
    file_path: str


class FactLoadResponse(BaseModel):
    records_loaded: int
    status: str


class FactLoadLogRead(BaseModel):
    id: int
    status: str
    records_loaded: int
    message: str | None = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class CompareRow(BaseModel):
    period: str | None = None
    construction_object_id: int | None = None
    metric: str
    version_a: float
    version_b: float
    variance: float
    variance_percent: float | None
