from datetime import datetime
from pydantic import BaseModel


class BranchRead(BaseModel):
    id: int
    name: str
    address: str
    phone: str | None
    is_active: bool
    created_at: datetime
