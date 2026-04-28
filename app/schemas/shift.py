from datetime import datetime
from pydantic import BaseModel


class ShiftCreate(BaseModel):
    initial_cash: float = 0.0


class ShiftClose(BaseModel):
    actual_cash: float
    notes: str | None = None


class ShiftRead(BaseModel):
    id: int
    branch_id: int
    opened_by: int
    closed_by: int | None
    opened_at: datetime
    closed_at: datetime | None
    initial_cash: float
    expected_cash: float
    actual_cash: float
    notes: str | None
    is_active: bool
