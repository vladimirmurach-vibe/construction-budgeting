"""Начальное наполнение БД: формы, пользователи, демо-объекты."""
from datetime import date

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.infrastructure.db.models import (
    CashFlowLine,
    CashFlowSource,
    ConstructionObject,
    InputForm,
    ObjectStatus,
    Scenario,
    ScenarioScope,
    ScenarioStatus,
    ScenarioType,
    User,
    UserRole,
)
from app.infrastructure.db.session import SessionLocal
from app.domain.services.consensus_service import ConsensusService


def seed_database():
    db: Session = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return

        forms = [
            InputForm(code="FORM-01", name="Денежные потоки — материалы", object_bound=True),
            InputForm(code="FORM-02", name="Денежные потоки — работы", object_bound=True),
            InputForm(code="FORM-03", name="Выручка", object_bound=True),
        ]
        db.add_all(forms)

        obj_a = ConstructionObject(
            name="Объект А",
            code="OBJ-A",
            construction_start=date(2025, 1, 1),
            construction_end=date(2027, 6, 30),
            status=ObjectStatus.in_progress,
        )
        obj_b = ConstructionObject(
            name="ЖК Северный",
            code="OBJ-001",
            construction_start=date(2025, 6, 1),
            construction_end=date(2028, 12, 31),
            status=ObjectStatus.planning,
        )
        db.add_all([obj_a, obj_b])
        db.flush()

        users = [
            User(
                email="admin@example.com",
                full_name="Администратор",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.admin,
            ),
            User(
                email="analyst@example.com",
                full_name="Бюджетный аналитик",
                hashed_password=get_password_hash("valid_password"),
                role=UserRole.budget_analyst,
            ),
            User(
                email="manager@example.com",
                full_name="Руководитель объекта",
                hashed_password=get_password_hash("manager123"),
                role=UserRole.project_manager,
                construction_object_id=obj_a.id,
            ),
            User(
                email="mgmt@example.com",
                full_name="Менеджмент",
                hashed_password=get_password_hash("mgmt123"),
                role=UserRole.management,
            ),
        ]
        db.add_all(users)

        scenario = Scenario(
            name="Демо-сценарий",
            type=ScenarioType.budget,
            scope=ScenarioScope.all_objects,
            version_number=1,
            status=ScenarioStatus.draft,
        )
        db.add(scenario)
        db.flush()

        consensus = ConsensusService()
        sample_lines = [
            ("FORM-01", "Материалы", "2026-01", 100000, 0, obj_a.id),
            ("FORM-01", "Материалы", "2026-02", 120000, 0, obj_a.id),
            ("FORM-01", "Материалы", "2026-03", 150000, 0, obj_a.id),
            ("FORM-02", "Работы", "2026-01", 80000, 0, obj_a.id),
            ("FORM-02", "Работы", "2026-02", 90000, 0, obj_a.id),
            ("FORM-03", "Выручка", "2026-01", 300000, 0, obj_a.id),
            ("FORM-03", "Выручка", "2026-02", 350000, 0, obj_a.id),
            ("FORM-01", "Материалы", "2026-01", 200000, 0, obj_b.id),
            ("FORM-02", "Работы", "2026-01", 150000, 0, obj_b.id),
            ("FORM-03", "Выручка", "2026-01", 500000, 0, obj_b.id),
        ]
        for form_code, line_item, period, base, adj, obj_id in sample_lines:
            db.add(
                CashFlowLine(
                    scenario_id=scenario.id,
                    construction_object_id=obj_id,
                    form_code=form_code,
                    line_item=line_item,
                    period=period,
                    base_amount=base,
                    adjustment=adj,
                    consensus_amount=float(consensus.calculate_for_record(base, adj)),
                    source=CashFlowSource.manual,
                )
            )

        db.commit()
    finally:
        db.close()
