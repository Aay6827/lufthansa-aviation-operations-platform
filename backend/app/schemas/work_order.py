from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WorkOrderCreate(BaseModel):

    aircraft_id: int = Field(gt=0)
    title: str = Field(min_length=4, max_length=160)
    description: str | None = None
    priority: str = Field(
        default="normal",
        pattern="^(low|normal|high|critical)$"
    )
    status: str = Field(
        default="open",
        pattern="^(open|in_progress|blocked|completed|cancelled)$"
    )
    due_date: date


class WorkOrderUpdate(BaseModel):
    status: str | None = Field(
        default=None,
        pattern="^(open|in_progress|blocked|completed|cancelled)$"
    )
    priority: str | None = Field(
        default=None,
        pattern="^(low|normal|high|critical)$"
    )

    @model_validator(mode="after")
    def validate_update(self):
        if self.status is None and self.priority is None:
            raise ValueError("At least one field must be provided")
        return self


class WorkOrderRead(BaseModel):
    id: int
    work_order_number: str
    aircraft_id: int
    title: str
    description: str | None
    priority: str
    status: str
    due_date: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)