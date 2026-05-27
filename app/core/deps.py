from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_session
from app.models.base import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@dataclass
class AuthContext:
    id: int
    email: str
    full_name: str
    is_active: bool
    role: str
    branch_id: int | None


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep,
) -> AuthContext:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        if payload.get("type") == "pending":
            raise credentials_exception
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await session.get(User, int(user_id))
    if user is None or not user.is_active:
        raise credentials_exception

    return AuthContext(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        role=payload["role"],
        branch_id=payload.get("branch_id"),
    )


CurrentUser = Annotated[AuthContext, Depends(get_current_user)]


def require_roles(*roles: str):
    async def _check(current_user: CurrentUser) -> AuthContext:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return _check


AdminDep = Annotated[AuthContext, Depends(require_roles("admin"))]
ManagerDep = Annotated[AuthContext, Depends(require_roles("admin", "manager"))]
CashierDep = Annotated[AuthContext, Depends(require_roles("admin", "manager", "cashier"))]
WaiterDep = Annotated[AuthContext, Depends(require_roles("admin", "manager", "waiter", "cashier"))]
KitchenDep = Annotated[AuthContext, Depends(require_roles("admin", "manager", "kitchen"))]
