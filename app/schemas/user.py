from pydantic import BaseModel, EmailStr


class BranchMembershipCreate(BaseModel):
    branch_id: int | None = None
    role: str = "waiter"


class BranchMembershipRead(BaseModel):
    id: int
    branch_id: int | None
    branch_name: str | None
    role: str
    is_active: bool


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    memberships: list[BranchMembershipCreate] = []


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = None


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    memberships: list[BranchMembershipRead] = []
