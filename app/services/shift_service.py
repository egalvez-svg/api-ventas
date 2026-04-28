from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import generate_refresh_token, hash_token
from app.models.base import RefreshToken, Shift, User

ADMIN_REFRESH_DAYS = 7
NO_SHIFT_REFRESH_HOURS = 1


async def get_active_shift(branch_id: int, session: AsyncSession) -> Shift | None:
    result = await session.exec(
        select(Shift).where(Shift.branch_id == branch_id, Shift.is_active == True)
    )
    return result.first()


async def open_shift(branch_id: int, user_id: int, session: AsyncSession) -> Shift:
    existing = await get_active_shift(branch_id, session)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="There is already an active shift for this branch",
        )
    shift = Shift(branch_id=branch_id, opened_by=user_id)
    session.add(shift)
    await session.commit()
    await session.refresh(shift)
    return shift


async def close_shift(branch_id: int, user_id: int, session: AsyncSession) -> Shift:
    shift = await get_active_shift(branch_id, session)
    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active shift found for this branch",
        )
    shift.is_active = False
    shift.closed_at = datetime.utcnow()
    shift.closed_by = user_id
    session.add(shift)
    await session.commit()
    await session.refresh(shift)
    return shift


async def create_refresh_token(
    user_id: int,
    role: str,
    branch_id: int | None,
    session: AsyncSession,
    shift: Shift | None = None,
) -> str:
    raw_token = generate_refresh_token()
    token_hash = hash_token(raw_token)

    expires_at: datetime | None = None
    shift_id: int | None = None

    if role == "admin":
        expires_at = datetime.utcnow() + timedelta(days=ADMIN_REFRESH_DAYS)
    elif shift:
        shift_id = shift.id
    else:
        expires_at = datetime.utcnow() + timedelta(hours=NO_SHIFT_REFRESH_HOURS)

    record = RefreshToken(
        token_hash=token_hash,
        user_id=user_id,
        role=role,
        branch_id=branch_id,
        shift_id=shift_id,
        expires_at=expires_at,
    )
    session.add(record)
    await session.commit()
    return raw_token


async def validate_and_rotate_refresh_token(
    raw_token: str,
    session: AsyncSession,
) -> tuple[RefreshToken, User, str]:
    token_hash = hash_token(raw_token)
    result = await session.exec(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    record = result.first()

    if not record or record.is_revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if record.shift_id is not None:
        shift = await session.get(Shift, record.shift_id)
        if not shift or not shift.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Shift has been closed — please log in again",
            )
    elif record.expires_at is not None:
        if datetime.utcnow() > record.expires_at:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    user = await session.get(User, record.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    record.is_revoked = True
    session.add(record)

    shift_obj: Shift | None = None
    if record.shift_id:
        shift_obj = await session.get(Shift, record.shift_id)

    new_raw = await create_refresh_token(record.user_id, record.role, record.branch_id, session, shift=shift_obj)
    return record, user, new_raw
