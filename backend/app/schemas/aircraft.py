from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AircraftCreate(BaseModel):
    registration: str = Field(min_length=3, max_length=16, examples=["D-AIXX"])
    aircraft_type: str = Field(min_length=2, max_length=80, examples=["A320neo"])
    manufacturer: str = Field(min_length=2, max_length=80, examples=["Airbus"])
    status: str = Field(default="operational", pattern="^(operational|maintenance|grounded)$")


class AircraftRead(BaseModel):
    id: int
    registration: str
    aircraft_type: str
    manufacturer: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
