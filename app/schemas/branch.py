from datetime import datetime
from pydantic import BaseModel


class BranchCreate(BaseModel):
    name: str
    address: str
    phone: str | None = None


class BranchUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    is_active: bool | None = None


class BranchRead(BaseModel):
    id: int
    name: str
    address: str
    phone: str | None
    is_active: bool
    created_at: datetime
