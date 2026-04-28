from pydantic import BaseModel


class BranchOption(BaseModel):
    branch_id: int | None
    branch_name: str | None
    role: str


class Token(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"
    shift_id: int | None = None
    # Populated when user has multiple branch memberships — front must call /auth/select-branch
    pending_token: str | None = None
    memberships: list[BranchOption] = []


class RefreshRequest(BaseModel):
    refresh_token: str


class SelectBranchRequest(BaseModel):
    pending_token: str
    branch_id: int | None
    role: str


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
