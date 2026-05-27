from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CashierDep, CurrentUser, ManagerDep, SessionDep
from app.schemas.sales import OrderRead
from app.schemas.shift import ShiftClose, ShiftCreate, ShiftRead
from app.services.order_service import order_service
from app.services.shift_service import close_shift, get_active_shift, get_shift_by_id, list_shifts, open_shift

router = APIRouter(prefix="/branches/{branch_id}/shifts", tags=["Shifts"])


@router.get("", response_model=list[ShiftRead])
async def list_branch_shifts(
    branch_id: int,
    session: SessionDep,
    user: ManagerDep,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Historial de turnos de la sucursal (manager/admin)."""
    if user.role == "manager" and user.branch_id != branch_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to this branch is not allowed")
    return await list_shifts(branch_id, session, skip, limit)


@router.get("/current", response_model=ShiftRead | None)
async def current_shift(branch_id: int, session: SessionDep, _: CurrentUser):
    return await get_active_shift(branch_id, session)


@router.get("/current/orders", response_model=list[OrderRead])
async def current_shift_orders(branch_id: int, session: SessionDep, user: CashierDep):
    """Órdenes del turno activo (cajero/manager/admin)."""
    if user.role not in ("admin",) and user.branch_id != branch_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to this branch is not allowed")
    shift = await get_active_shift(branch_id, session)
    if not shift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active shift for this branch")
    return await order_service.list_by_shift(session, branch_id, shift.id, user)


@router.get("/{shift_id}/orders", response_model=list[OrderRead])
async def shift_orders(branch_id: int, shift_id: int, session: SessionDep, user: ManagerDep):
    """Órdenes de un turno específico (manager/admin)."""
    if user.role == "manager" and user.branch_id != branch_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to this branch is not allowed")
    shift = await get_shift_by_id(branch_id, shift_id, session)
    return await order_service.list_by_shift(session, branch_id, shift.id, user)


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
