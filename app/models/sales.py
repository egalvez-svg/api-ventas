from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class Table(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    number: str
    branch_id: int = Field(foreign_key="branch.id")
    status: str = Field(default="available")  # available, occupied, reserved


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id")
    table_id: Optional[int] = Field(default=None, foreign_key="table.id")
    user_id: int = Field(foreign_key="user.id")
    shift_id: Optional[int] = Field(default=None, foreign_key="shift.id")
    status: str = Field(default="pending")  # pending, cooking, served, paid, cancelled
    total: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    items: List["OrderItem"] = Relationship(back_populates="order", sa_relationship_kwargs={"lazy": "raise"})
    shift: Optional["Shift"] = Relationship(back_populates="orders", sa_relationship_kwargs={"lazy": "raise"})


class OrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    product_id: int = Field(foreign_key="product.id")
    quantity: int = 1
    price: float
    notes: Optional[str] = None

    order: Order = Relationship(back_populates="items", sa_relationship_kwargs={"lazy": "raise"})
    extras: List["OrderItemExtra"] = Relationship(back_populates="order_item", sa_relationship_kwargs={"lazy": "raise"})


class OrderItemExtra(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_item_id: int = Field(foreign_key="orderitem.id")
    ingredient_id: int = Field(foreign_key="ingredient.id")
    quantity: float

    order_item: OrderItem = Relationship(back_populates="extras", sa_relationship_kwargs={"lazy": "raise"})
