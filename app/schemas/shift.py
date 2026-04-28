from datetime import datetime
from pydantic import BaseModel


class ShiftRead(BaseModel):
    id: int
    branch_id: int
    opened_by: int
    closed_by: int | None
    opened_at: datetime
    closed_at: datetime | None
    is_active: bool
