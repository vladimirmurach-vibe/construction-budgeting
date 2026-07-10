from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.infrastructure.db.models import FinancialResult
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/scenarios", tags=["compare"])


def _compare_data(db: Session, version_a: UUID, version_b: UUID, construction_object_id: UUID | None = None):
    def fetch(scenario_id):
        if construction_object_id:
            q = db.query(FinancialResult).filter(
                FinancialResult.scenario_id == scenario_id,
                FinancialResult.construction_object_id == construction_object_id,
            )
        else:
            q = db.query(FinancialResult).filter(
                FinancialResult.scenario_id == scenario_id,
                FinancialResult.is_consolidated == True,  # noqa: E712
            )
        return {r.period: r for r in q.all()}

    a_data = fetch(version_a)
    b_data = fetch(version_b)
    periods = sorted(set(a_data.keys()) | set(b_data.keys()))
    result = []
    for period in periods:
        ra = a_data.get(period)
        rb = b_data.get(period)
        amount_a = float(ra.profit) if ra else 0
        amount_b = float(rb.profit) if rb else 0
        variance = amount_b - amount_a
        variance_percent = (variance / amount_a * 100) if amount_a else 0
        result.append({
            "period": period,
            "amount_a": amount_a,
            "amount_b": amount_b,
            "variance": variance,
            "variance_percent": variance_percent,
        })
    return result


@router.get("/compare")
def compare_versions(
    version_a: UUID = Query(...),
    version_b: UUID = Query(...),
    construction_object_id: UUID | None = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return _compare_data(db, version_a, version_b, construction_object_id)


@router.get("/compare/chart")
def compare_chart(
    version_a: UUID = Query(...),
    version_b: UUID = Query(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    data = _compare_data(db, version_a, version_b)
    return {
        "categories": [r["period"] for r in data],
        "series": [
            {"name": "Версия A", "data": [r["amount_a"] for r in data]},
            {"name": "Версия B", "data": [r["amount_b"] for r in data]},
        ],
    }
