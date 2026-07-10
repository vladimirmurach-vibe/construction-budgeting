from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.infrastructure.db.models import ConstructionObject, User
from app.infrastructure.db.session import get_db
from app.presentation.api.deps import get_current_user
from app.presentation.api.schemas import (
    ConstructionObjectCreate,
    ConstructionObjectRead,
    ConstructionObjectUpdate,
)


router = APIRouter(prefix="/construction-objects", tags=["construction-objects"])


@router.get("", response_model=list[ConstructionObjectRead])
def list_objects(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return db.query(ConstructionObject).order_by(ConstructionObject.code).all()


@router.post("", response_model=ConstructionObjectRead, status_code=status.HTTP_201_CREATED)
def create_object(
    payload: ConstructionObjectCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    obj = ConstructionObject(**payload.model_dump())
    db.add(obj)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail="construction object code must be unique") from exc
    db.refresh(obj)
    return obj


@router.get("/{object_id}", response_model=ConstructionObjectRead)
def get_object(
    object_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    obj = db.get(ConstructionObject, object_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Construction object not found")
    return obj


@router.patch("/{object_id}", response_model=ConstructionObjectRead)
def update_object(
    object_id: int,
    payload: ConstructionObjectUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    obj = db.get(ConstructionObject, object_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Construction object not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    if obj.construction_end < obj.construction_start:
        raise HTTPException(status_code=422, detail="construction_end must be greater than start")
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail="construction object code must be unique") from exc
    db.refresh(obj)
    return obj


@router.delete("/{object_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_object(
    object_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    obj = db.get(ConstructionObject, object_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Construction object not found")
    db.delete(obj)
    db.commit()
    return None
