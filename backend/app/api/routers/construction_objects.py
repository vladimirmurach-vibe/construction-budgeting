from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.api.schemas import ConstructionObjectCreate, ConstructionObjectResponse
from app.infrastructure.db.models import ConstructionObject, User, UserRole
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/construction-objects", tags=["construction-objects"])


@router.get("", response_model=list[ConstructionObjectResponse])
def list_objects(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(ConstructionObject)
    if user.role == UserRole.project_manager and user.construction_object_id:
        query = query.filter(ConstructionObject.id == user.construction_object_id)
    return query.order_by(ConstructionObject.code).all()


@router.post("", response_model=ConstructionObjectResponse, status_code=status.HTTP_201_CREATED)
def create_object(
    body: ConstructionObjectCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.budget_analyst)),
):
    if db.query(ConstructionObject).filter(ConstructionObject.code == body.code).first():
        raise HTTPException(status_code=422, detail="Object code must be unique")
    obj = ConstructionObject(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{object_id}", response_model=ConstructionObjectResponse)
def get_object(object_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(ConstructionObject).filter(ConstructionObject.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    if user.role == UserRole.project_manager and user.construction_object_id != object_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return obj
