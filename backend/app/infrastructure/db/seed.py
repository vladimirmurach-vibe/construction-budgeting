from datetime import date

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.infrastructure.db.models import (
    CashFlowLine,
    ConstructionObject,
    InputForm,
    Scenario,
    User,
)


SEED_USERS = [
    ("analyst@example.com", "valid_password", "budget_analyst"),
    ("admin@example.com", "admin123", "admin"),
    ("manager@example.com", "manager123", "project_manager"),
    ("mgmt@example.com", "mgmt123", "management"),
]


def seed_database(db: Session) -> None:
    seed_users(db)
    objects = seed_construction_objects(db)
    seed_input_forms(db)
    seed_demo_scenario(db, objects)
    db.commit()


def seed_users(db: Session) -> None:
    for email, password, role in SEED_USERS:
        if not db.query(User).filter(User.email == email).first():
            db.add(User(email=email, hashed_password=hash_password(password), role=role))


def seed_construction_objects(db: Session) -> list[ConstructionObject]:
    seeds = [
        ConstructionObject(
            name="Объект А",
            code="OBJ-001",
            construction_start=date(2026, 1, 1),
            construction_end=date(2026, 6, 30),
            status="in_progress",
        ),
        ConstructionObject(
            name="Объект Б",
            code="OBJ-002",
            construction_start=date(2026, 2, 1),
            construction_end=date(2026, 9, 30),
            status="in_progress",
        ),
    ]
    for obj in seeds:
        if not db.query(ConstructionObject).filter(ConstructionObject.code == obj.code).first():
            db.add(obj)
    db.flush()
    return db.query(ConstructionObject).order_by(ConstructionObject.code).all()


def seed_input_forms(db: Session) -> None:
    forms = [
        ("FORM-01", "Форма-01: Доходы и материалы"),
        ("FORM-02", "Форма-02: Подрядные работы"),
    ]
    for code, name in forms:
        if not db.query(InputForm).filter(InputForm.code == code).first():
            db.add(InputForm(code=code, name=name, is_required=True))


def seed_demo_scenario(db: Session, objects: list[ConstructionObject]) -> None:
    if db.query(Scenario).filter(Scenario.name == "Демо бюджет 2026").first():
        return

    scenario = Scenario(name="Демо бюджет 2026", type="budget", scope="all_objects", version_number=1)
    db.add(scenario)
    db.flush()

    for index, obj in enumerate(objects[:2], start=1):
        revenue_base = 1_000_000.0 * index
        material_base = 350_000.0 * index
        works_base = 250_000.0 * index
        for period in ["2026-02", "2026-03", "2026-04"]:
            db.add_all(
                [
                    CashFlowLine(
                        scenario_id=scenario.id,
                        construction_object_id=obj.id,
                        form_code="FORM-01",
                        line_item="Revenue",
                        period=period,
                        base_amount=revenue_base,
                        adjustment=0,
                        consensus_amount=revenue_base,
                        source="manual",
                    ),
                    CashFlowLine(
                        scenario_id=scenario.id,
                        construction_object_id=obj.id,
                        form_code="FORM-01",
                        line_item="Материалы",
                        period=period,
                        base_amount=material_base,
                        adjustment=0,
                        consensus_amount=material_base,
                        source="manual",
                    ),
                    CashFlowLine(
                        scenario_id=scenario.id,
                        construction_object_id=obj.id,
                        form_code="FORM-02",
                        line_item="Подрядные работы",
                        period=period,
                        base_amount=works_base,
                        adjustment=0,
                        consensus_amount=works_base,
                        source="manual",
                    ),
                ]
            )
