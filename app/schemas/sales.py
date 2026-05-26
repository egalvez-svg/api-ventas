from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel


class TableCreate(SQLModel):
    number: str
    status: str = "available"


class TableRead(SQLModel):
    id: int
    number: str
    branch_id: int
    status: str


class TableUpdate(SQLModel):
    number: Optional[str] = None
    status: Optional[str] = None


class OrderItemExtraCreate(SQLModel):
    ingredient_id: int
    quantity: float


class OrderItemExtraRead(SQLModel):
    ingredient_id: int
    quantity: float


class OrderItemCreate(SQLModel):
    product_id: int
    quantity: int = 1
    notes: Optional[str] = None
    extras: list[OrderItemExtraCreate] = []


class OrderItemRead(SQLModel):
    id: int
    product_id: int
    quantity: int
    price: float
    notes: Optional[str] = None
    extras: list[OrderItemExtraRead] = []


class OrderCreate(SQLModel):
    table_id: Optional[int] = None
    items: list[OrderItemCreate]


class OrderRead(SQLModel):
    id: int
    branch_id: int
    table_id: Optional[int] = None
    user_id: int
    status: str
    total: float
    tip: float = 0.0
    created_at: datetime
    items: list[OrderItemRead] = []


class OrderStatusUpdate(SQLModel):
    status: str
    tip: float = 0.0


class TablePayRequest(SQLModel):
    tip: float = 0.0


class TableInvoiceRead(SQLModel):
    table_id: int
    branch_id: int
    orders: list[OrderRead]
    subtotal: float
    tip: float
    total: float
