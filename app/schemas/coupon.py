from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel


class CouponBase(SQLModel):
    code: str
    description: str
    discount_type: str  # percentage, fixed
    discount_value: float
    min_order_value: float = 0.0
    expiration_date: datetime
    max_uses: Optional[int] = None
    is_active: bool = True


class CouponCreate(CouponBase):
    pass


class CouponUpdate(SQLModel):
    code: Optional[str] = None
    description: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    min_order_value: Optional[float] = None
    expiration_date: Optional[datetime] = None
    max_uses: Optional[int] = None
    is_active: Optional[bool] = None


class CouponRead(CouponBase):
    id: int
    used_count: int
    branch_id: Optional[int]
    created_at: datetime
