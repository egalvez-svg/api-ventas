from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlmodel import select

from app.core.deps import CurrentUser, SessionDep
from app.core.security import create_access_token, decode_access_token, verify_password
from app.models.base import Branch, User, UserBranchRole
from app.schemas.auth import BranchOption, RefreshRequest, SelectBranchRequest, Token
from app.schemas.user import BranchMembershipRead, UserRead
from app.services.shift_service import (
    create_refresh_token,
    get_active_shift,
    validate_and_rotate_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

FormData = Annotated[OAuth2PasswordRequestForm, Depends()]

PENDING_TOKEN_MINUTES = 5


async def _build_user_read(user_id: int, session) -> UserRead:
    user = await session.get(User, user_id)
    memberships_result = await session.exec(
        select(UserBranchRole).where(UserBranchRole.user_id == user_id)
    )
    memberships = memberships_result.all()
    membership_reads = []
    for m in memberships:
        branch_name = None
        if m.branch_id:
            branch = await session.get(Branch, m.branch_id)
            branch_name = branch.name if branch else None
        membership_reads.append(BranchMembershipRead(
            id=m.id, branch_id=m.branch_id, branch_name=branch_name,
            role=m.role, is_active=m.is_active,
        ))
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        memberships=membership_reads,
    )


@router.post("/login", response_model=Token)
async def login(form_data: FormData, session: SessionDep):
    result = await session.exec(select(User).where(User.email == form_data.username))
    user = result.first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    memberships_result = await session.exec(
        select(UserBranchRole).where(
            UserBranchRole.user_id == user.id,
            UserBranchRole.is_active == True,
        )
    )
    memberships = memberships_result.all()

    if not memberships:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No active branch memberships")

    if len(memberships) == 1:
        m = memberships[0]
        shift = await get_active_shift(m.branch_id, session) if m.branch_id else None
        refresh_token = await create_refresh_token(user.id, m.role, m.branch_id, session, shift=shift)
        access_token = create_access_token({"sub": str(user.id), "branch_id": m.branch_id, "role": m.role})
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            shift_id=shift.id if shift else None,
        )

    # Multiple memberships — issue short-lived pending token, front must call /auth/select-branch
    pending_token = create_access_token(
        {"sub": str(user.id), "type": "pending"},
        expire_minutes=PENDING_TOKEN_MINUTES,
    )
    options = []
    for m in memberships:
        branch_name = None
        if m.branch_id:
            branch = await session.get(Branch, m.branch_id)
            branch_name = branch.name if branch else None
        options.append(BranchOption(branch_id=m.branch_id, branch_name=branch_name, role=m.role))

    return Token(pending_token=pending_token, memberships=options)


@router.post("/select-branch", response_model=Token)
async def select_branch(body: SelectBranchRequest, session: SessionDep):
    try:
        payload = decode_access_token(body.pending_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid pending token")

    if payload.get("type") != "pending":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid pending token")

    user_id = int(payload["sub"])

    membership_result = await session.exec(
        select(UserBranchRole).where(
            UserBranchRole.user_id == user_id,
            UserBranchRole.branch_id == body.branch_id,
            UserBranchRole.role == body.role,
            UserBranchRole.is_active == True,
        )
    )
    membership = membership_result.first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Membership not found")

    user = await session.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    shift = await get_active_shift(body.branch_id, session) if body.branch_id else None
    refresh_token = await create_refresh_token(user.id, body.role, body.branch_id, session, shift=shift)
    access_token = create_access_token({"sub": str(user_id), "branch_id": body.branch_id, "role": body.role})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        shift_id=shift.id if shift else None,
    )


@router.post("/refresh", response_model=Token)
async def refresh(body: RefreshRequest, session: SessionDep):
    old_record, user, new_refresh_token = await validate_and_rotate_refresh_token(
        body.refresh_token, session
    )

    shift = None
    if old_record.branch_id:
        shift = await get_active_shift(old_record.branch_id, session)

    access_token = create_access_token({
        "sub": str(user.id),
        "branch_id": old_record.branch_id,
        "role": old_record.role,
    })

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        shift_id=shift.id if shift else None,
    )


@router.get("/me", response_model=UserRead)
async def me(current_user: CurrentUser, session: SessionDep):
    return await _build_user_read(current_user.id, session)
