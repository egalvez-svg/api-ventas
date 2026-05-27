from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.core.deps import CurrentUser, SessionDep, require_roles
from app.core.security import get_password_hash
from app.models.base import Branch, User, UserBranchRole
from app.schemas.user import BranchMembershipCreate, BranchMembershipRead, UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])

AdminOnly = Depends(require_roles("admin"))
AdminOrManager = Depends(require_roles("admin", "manager"))

# Roles que un manager NO puede asignar (previene escalación de privilegios)
_MANAGER_FORBIDDEN_ROLES = {"admin"}


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


async def _assert_user_in_branch(user_id: int, branch_id: int, session) -> None:
    """Lanza 403 si el usuario no tiene membresía en la sucursal indicada."""
    result = await session.exec(
        select(UserBranchRole).where(
            UserBranchRole.user_id == user_id,
            UserBranchRole.branch_id == branch_id,
        )
    )
    if not result.first():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


async def _assert_target_not_admin(user_id: int, session) -> None:
    """Lanza 403 si el usuario objetivo tiene algún rol admin (managers no pueden verlo ni modificarlo)."""
    result = await session.exec(
        select(UserBranchRole).where(
            UserBranchRole.user_id == user_id,
            UserBranchRole.role == "admin",
        )
    )
    if result.first():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


def _assert_manager_branch_id(current_user) -> int:
    """Retorna branch_id del manager o lanza error si no tiene sucursal asignada."""
    if not current_user.branch_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager has no branch assigned")
    return current_user.branch_id


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate, session: SessionDep, current_user: CurrentUser):
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    if current_user.role == "manager":
        branch_id = _assert_manager_branch_id(current_user)
        for m in user_in.memberships:
            if m.branch_id != branch_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Manager solo puede crear usuarios para su propia sucursal",
                )
            if m.role in _MANAGER_FORBIDDEN_ROLES:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Manager no puede asignar el rol '{m.role}'",
                )

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


@router.get("/", response_model=list[UserRead])
async def list_users(session: SessionDep, current_user: CurrentUser):
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    if current_user.role == "admin":
        result = await session.exec(select(User))
        users = result.all()
    else:
        branch_id = _assert_manager_branch_id(current_user)
        memberships_result = await session.exec(
            select(UserBranchRole).where(UserBranchRole.branch_id == branch_id)
        )
        user_ids = {m.user_id for m in memberships_result.all()}
        # Excluir usuarios que tengan algún rol admin
        admin_memberships_result = await session.exec(
            select(UserBranchRole).where(UserBranchRole.role == "admin")
        )
        admin_user_ids = {m.user_id for m in admin_memberships_result.all()}
        user_ids -= admin_user_ids
        result = await session.exec(select(User).where(User.id.in_(user_ids)))
        users = result.all()

    return [await _build_user_read(u, session) for u in users]


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, session: SessionDep, current_user: CurrentUser):
    if current_user.role == "admin":
        pass
    elif current_user.role == "manager":
        await _assert_target_not_admin(user_id, session)
        await _assert_user_in_branch(user_id, _assert_manager_branch_id(current_user), session)
    elif current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return await _build_user_read(user, session)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(user_id: int, user_in: UserUpdate, session: SessionDep, current_user: CurrentUser):
    if current_user.role == "admin":
        pass
    elif current_user.role == "manager":
        await _assert_target_not_admin(user_id, session)
        await _assert_user_in_branch(user_id, _assert_manager_branch_id(current_user), session)
    elif current_user.id != user_id:
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
        if current_user.role not in ("admin", "manager"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin or manager can update memberships")

        if current_user.role == "manager":
            branch_id = _assert_manager_branch_id(current_user)
            for m in user_in.memberships:
                if m.branch_id != branch_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Manager solo puede gestionar membresías de su propia sucursal",
                    )
                if m.role in _MANAGER_FORBIDDEN_ROLES:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Manager no puede asignar el rol '{m.role}'",
                    )
            # Solo reemplaza membresías de la sucursal del manager; deja las demás intactas
            existing_memberships = await session.exec(
                select(UserBranchRole).where(
                    UserBranchRole.user_id == user_id,
                    UserBranchRole.branch_id == branch_id,
                )
            )
            for m in existing_memberships.all():
                await session.delete(m)
        else:
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
    if current_user.role == "admin":
        pass
    elif current_user.role == "manager":
        await _assert_target_not_admin(user_id, session)
        await _assert_user_in_branch(user_id, _assert_manager_branch_id(current_user), session)
    else:
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
)
async def add_membership(user_id: int, membership_in: BranchMembershipCreate, session: SessionDep, current_user: CurrentUser):
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    if current_user.role == "manager":
        await _assert_target_not_admin(user_id, session)
        branch_id = _assert_manager_branch_id(current_user)
        if membership_in.branch_id != branch_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Manager solo puede agregar membresías a su propia sucursal",
            )
        if membership_in.role in _MANAGER_FORBIDDEN_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Manager no puede asignar el rol '{membership_in.role}'",
            )

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
)
async def remove_membership(user_id: int, membership_id: int, session: SessionDep, current_user: CurrentUser):
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    membership = await session.get(UserBranchRole, membership_id)
    if not membership or membership.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")

    if current_user.role == "manager":
        await _assert_target_not_admin(user_id, session)
        if membership.branch_id != current_user.branch_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Manager solo puede eliminar membresías de su propia sucursal",
            )

    await session.delete(membership)
    await session.commit()
