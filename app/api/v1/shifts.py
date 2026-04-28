from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, ManagerDep, SessionDep
from app.schemas.shift import ShiftClose, ShiftCreate, ShiftRead
from app.services.shift_service import close_shift, get_active_shift, open_shift

router = APIRouter(prefix="/branches/{branch_id}/shifts", tags=["Shifts"])



@router.get("/current", response_model=ShiftRead | None)
async def current_shift(branch_id: int, session: SessionDep, _: CurrentUser):
    return await get_active_shift(branch_id, session)


@router.post("/open", response_model=ShiftRead, status_code=status.HTTP_201_CREATED)
async def open_branch_shift(
    branch_id: int,
    data: ShiftCreate,
    session: SessionDep,
    current_user: ManagerDep,
):
    if current_user.role == "manager" and current_user.branch_id != branch_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to this branch is not allowed")
    return await open_shift(branch_id, current_user.id, data.initial_cash, session)


@router.post("/close", response_model=ShiftRead)
async def close_branch_shift(
    branch_id: int,
    data: ShiftClose,
    session: SessionDep,
    current_user: ManagerDep,
):
    if current_user.role == "manager" and current_user.branch_id != branch_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to this branch is not allowed")
    return await close_shift(branch_id, current_user.id, data.actual_cash, data.notes, session)
