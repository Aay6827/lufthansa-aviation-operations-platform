from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.aircraft import Aircraft
from app.schemas.aircraft import AircraftCreate, AircraftRead

router = APIRouter(prefix="/aircraft", tags=["Aircraft"])


@router.post("", response_model=AircraftRead, status_code=status.HTTP_201_CREATED)
def create_aircraft(payload: AircraftCreate, db: Session = Depends(get_db)):
    aircraft = Aircraft(**payload.model_dump())
    db.add(aircraft)
    try:
        db.commit()
        db.refresh(aircraft)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Aircraft registration already exists")
    return aircraft


@router.get("", response_model=list[AircraftRead])
def list_aircraft(status_filter: str | None = None, db: Session = Depends(get_db)):
    query = select(Aircraft).order_by(Aircraft.registration)
    if status_filter:
        if status_filter not in {"operational", "maintenance", "grounded"}:
            raise HTTPException(status_code=400, detail="Invalid aircraft status filter")
        query = query.where(Aircraft.status == status_filter)
    return list(db.scalars(query).all())


@router.get("/{aircraft_id}", response_model=AircraftRead)
def get_aircraft(aircraft_id: int, db: Session = Depends(get_db)):
    aircraft = db.get(Aircraft, aircraft_id)
    if aircraft is None:
        raise HTTPException(status_code=404, detail="Aircraft not found")
    return aircraft
