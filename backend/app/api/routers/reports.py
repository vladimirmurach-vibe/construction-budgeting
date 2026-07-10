import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.api.schemas import ReportGenerateRequest, ReportResponse
from app.domain.services.completeness_validator import CompletenessValidator
from app.domain.services.report_service import ReportService
from app.infrastructure.db.models import Report, User, UserRole
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/reports", tags=["reports"])
report_service = ReportService()
completeness = CompletenessValidator()


@router.post("/generate", response_model=ReportResponse, status_code=201)
def generate_report(
    body: ReportGenerateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.budget_analyst, UserRole.management, UserRole.governance)),
):
    check = completeness.validate_scenario(db, body.scenario_id)
    if not check["is_complete"]:
        raise HTTPException(status_code=422, detail=f"Incomplete data: {check['missing']}")
    return report_service.generate(
        db, body.scenario_id, body.type, body.format, body.construction_object_id
    )


@router.get("", response_model=list[ReportResponse])
def list_reports(
    scenario_id: UUID | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Report)
    if scenario_id:
        query = query.filter(Report.scenario_id == scenario_id)
    return query.order_by(Report.generated_at.desc()).all()


@router.get("/{report_id}/download")
def download_report(report_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report not found")
    media = "application/pdf" if report.format.value == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return FileResponse(report.file_path, media_type=media, filename=os.path.basename(report.file_path))
