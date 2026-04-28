from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class Branch(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    address: str
    phone: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    memberships: List["UserBranchRole"] = Relationship(back_populates="branch", sa_relationship_kwargs={"lazy": "raise"})
    shifts: List["Shift"] = Relationship(back_populates="branch", sa_relationship_kwargs={"lazy": "raise"})


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    full_name: str
    hashed_password: str
    is_active: bool = Field(default=True)

    memberships: List["UserBranchRole"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "raise"})
    refresh_tokens: List["RefreshToken"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "raise"})


class UserBranchRole(SQLModel, table=True):
    __tablename__ = "userbranchrole"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    branch_id: Optional[int] = Field(default=None, foreign_key="branch.id", index=True)
    role: str  # admin, manager, waiter, kitchen, cashier
    is_active: bool = Field(default=True)

    user: Optional[User] = Relationship(back_populates="memberships", sa_relationship_kwargs={"lazy": "raise"})
    branch: Optional[Branch] = Relationship(back_populates="memberships", sa_relationship_kwargs={"lazy": "raise"})


class Shift(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    opened_by: int = Field(foreign_key="user.id")
    closed_by: Optional[int] = Field(default=None, foreign_key="user.id")
    opened_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = Field(default=None)
    initial_cash: float = Field(default=0.0)
    expected_cash: float = Field(default=0.0)
    actual_cash: float = Field(default=0.0)
    notes: Optional[str] = None
    is_active: bool = Field(default=True)

    branch: Optional[Branch] = Relationship(back_populates="shifts", sa_relationship_kwargs={"lazy": "raise"})
    refresh_tokens: List["RefreshToken"] = Relationship(back_populates="shift", sa_relationship_kwargs={"lazy": "raise"})
    orders: List["Order"] = Relationship(back_populates="shift", sa_relationship_kwargs={"lazy": "raise"})


class RefreshToken(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    token_hash: str = Field(unique=True, index=True)
    user_id: int = Field(foreign_key="user.id")
    role: str  # stored at creation so rotation doesn't need an extra join
    branch_id: Optional[int] = Field(default=None, foreign_key="branch.id")
    shift_id: Optional[int] = Field(default=None, foreign_key="shift.id")
    expires_at: Optional[datetime] = Field(default=None)
    is_revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="refresh_tokens", sa_relationship_kwargs={"lazy": "raise"})
    shift: Optional[Shift] = Relationship(back_populates="refresh_tokens", sa_relationship_kwargs={"lazy": "raise"})
