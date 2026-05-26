from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.core.deps import CurrentUser, SessionDep, require_roles
from app.core.security import get_password_hash
from app.models.base import Branch, User, UserBranchRole
from app.schemas.user import BranchMembershipCreate, BranchMembershipRead, UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])

AdminOnly = Depends(require_roles("admin"))


async def _build_user_read(user: User, session) -> UserRead:
    memberships_result = await session.exec(
        select(UserBranchRole).where(UserBranchRole.user_id == user.id)
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


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED, dependencies=[AdminOnly])
async def create_user(user_in: UserCreate, session: SessionDep):
    result = await session.exec(select(User).where(User.email == user_in.email))
    if result.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )
    session.add(user)
    await session.flush()

    for m in user_in.memberships:
        session.add(UserBranchRole(user_id=user.id, branch_id=m.branch_id, role=m.role))

    await session.commit()
    await session.refresh(user)
    return await _build_user_read(user, session)


@router.get("/", response_model=list[UserRead], dependencies=[AdminOnly])
async def list_users(session: SessionDep):
    result = await session.exec(select(User))
    users = result.all()
    return [await _build_user_read(u, session) for u in users]


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, session: SessionDep, current_user: CurrentUser):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return await _build_user_read(user, session)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(user_id: int, user_in: UserUpdate, session: SessionDep, current_user: CurrentUser):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_in.email and user_in.email != user.email:
        existing = await session.exec(select(User).where(User.email == user_in.email))
        if existing.first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user.email = user_in.email

    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.password is not None:
        user.hashed_password = get_password_hash(user_in.password)

    if user_in.memberships is not None:
        if current_user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can update memberships")
        existing_memberships = await session.exec(
            select(UserBranchRole).where(UserBranchRole.user_id == user_id)
        )
        for m in existing_memberships.all():
            await session.delete(m)
        await session.flush()
        for m in user_in.memberships:
            session.add(UserBranchRole(user_id=user_id, branch_id=m.branch_id, role=m.role))

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return await _build_user_read(user, session)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(user_id: int, session: SessionDep, current_user: CurrentUser):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    if current_user.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate your own account")

    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = False
    session.add(user)
    await session.commit()


@router.post(
    "/{user_id}/memberships",
    response_model=BranchMembershipRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[AdminOnly],
)
async def add_membership(user_id: int, membership_in: BranchMembershipCreate, session: SessionDep):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing_result = await session.exec(
        select(UserBranchRole).where(
            UserBranchRole.user_id == user_id,
            UserBranchRole.branch_id == membership_in.branch_id,
            UserBranchRole.role == membership_in.role,
        )
    )
    if existing_result.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Membership already exists")

    membership = UserBranchRole(user_id=user_id, branch_id=membership_in.branch_id, role=membership_in.role)
    session.add(membership)
    await session.commit()
    await session.refresh(membership)

    branch_name = None
    if membership.branch_id:
        branch = await session.get(Branch, membership.branch_id)
        branch_name = branch.name if branch else None

    return BranchMembershipRead(
        id=membership.id,
        branch_id=membership.branch_id,
        branch_name=branch_name,
        role=membership.role,
        is_active=membership.is_active,
    )


@router.delete(
    "/{user_id}/memberships/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[AdminOnly],
)
async def remove_membership(user_id: int, membership_id: int, session: SessionDep):
    membership = await session.get(UserBranchRole, membership_id)
    if not membership or membership.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    await session.delete(membership)
    await session.commit()
