
from datetime import date
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.aircraft import Aircraft
from app.models.work_order import WorkOrder
from app.schemas.work_order import (
    WorkOrderCreate,
    WorkOrderRead,
    WorkOrderUpdate,
)

router = APIRouter(prefix="/work-orders", tags=["Maintenance work orders"])


ALLOWED_STATUS_TRANSITIONS = {
    "open": {"in_progress", "cancelled"},
    "in_progress": {"blocked", "completed", "cancelled"},
    "blocked": {"in_progress", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


@router.post("", response_model=WorkOrderRead, status_code=status.HTTP_201_CREATED)
def create_work_order(
    payload: WorkOrderCreate,
    db: Session = Depends(get_db),
):
    if db.get(Aircraft, payload.aircraft_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Aircraft not found",
        )

    work_order = WorkOrder(
        **payload.model_dump(),
        work_order_number=f"TEMP-{uuid4().hex}",
    )
    db.add(work_order)
    db.flush()

    work_order.work_order_number = (
        f"WO-{date.today().year}-{work_order.id:04d}"
    )

    db.commit()
    db.refresh(work_order)

    return work_order


@router.get("", response_model=list[WorkOrderRead])
def list_work_orders(
    status_filter: str | None = None,
    overdue_only: bool = False,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_by: Literal[
        "due_date",
        "created_at",
        "work_order_number",
    ] = "due_date",
    sort_order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
):
    query = select(WorkOrder)

    if status_filter:
        if status_filter not in {
            "open",
            "in_progress",
            "blocked",
            "completed",
            "cancelled",
        }:
            raise HTTPException(
                status_code=400,
                detail="Invalid work order status filter",
            )

        query = query.where(WorkOrder.status == status_filter)

    if overdue_only:
        query = query.where(
            WorkOrder.due_date < date.today(),
            WorkOrder.status.notin_(["completed", "cancelled"]),
        )

    sort_column = getattr(WorkOrder, sort_by)

    sort_expression = (
        sort_column.desc()
        if sort_order == "desc"
        else sort_column.asc()
    )

    query = (
        query
        .order_by(sort_expression)
        .offset(offset)
        .limit(limit)
    )

    return list(db.scalars(query).all())


@router.get("/{work_order_id}", response_model=WorkOrderRead)
def get_work_order(
    work_order_id: int,
    db: Session = Depends(get_db),
):
    work_order = db.get(WorkOrder, work_order_id)

    if work_order is None:
        raise HTTPException(
            status_code=404,
            detail="Work order not found",
        )

    return work_order


@router.patch("/{work_order_id}", response_model=WorkOrderRead)
def update_work_order(
    work_order_id: int,
    payload: WorkOrderUpdate,
    db: Session = Depends(get_db),
):
    work_order = db.get(WorkOrder, work_order_id)

    if work_order is None:
        raise HTTPException(
            status_code=404,
            detail="Work order not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    requested_status = update_data.get("status")

    if requested_status is not None and requested_status != work_order.status:
        allowed_statuses = ALLOWED_STATUS_TRANSITIONS[work_order.status]

        if requested_status not in allowed_statuses:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Cannot transition work order from "
                    f"'{work_order.status}' to '{requested_status}'"
                ),
            )

    for field, value in update_data.items():
        setattr(work_order, field, value)

    db.commit()
    db.refresh(work_order)

    return work_order
