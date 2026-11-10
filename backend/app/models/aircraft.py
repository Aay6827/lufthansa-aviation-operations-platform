from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Aircraft(Base):
    __tablename__ = "aircraft"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    registration: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    aircraft_type: Mapped[str] = mapped_column(String(80), index=True)
    manufacturer: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(24), default="operational", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
