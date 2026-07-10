from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.services.report_service import ReportService
from app.infrastructure.db.models import FinancialResult, Report, Scenario, User
from app.infrastructure.db.session import get_db
from app.presentation.api.deps import get_current_user
from app.presentation.api.schemas import ReportGenerateRequest, ReportRead


router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
def generate_report(
    payload: ReportGenerateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    scenario = db.get(Scenario, payload.scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")

    settings = get_settings()
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    suffix = "xlsx" if payload.format == "excel" else "pdf"
    file_path = settings.reports_dir / f"scenario_{scenario.id}_{payload.type}.{suffix}"
    results = (
        db.query(FinancialResult)
        .filter(FinancialResult.scenario_id == scenario.id)
        .order_by(FinancialResult.period)
        .all()
    )

    service = ReportService()
    if payload.format == "excel":
        service.generate_excel(file_path, scenario, results)
    else:
        service.generate_pdf(file_path, scenario, results)

    report = Report(
        scenario_id=scenario.id,
        type=payload.type,
        format=payload.format,
        file_path=str(file_path),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/{report_id}/download")
def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    path = Path(report.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    return FileResponse(path)
