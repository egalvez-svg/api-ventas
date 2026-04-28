from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import ManagerDep, SessionDep
from app.schemas.inventory import BranchStockRead, BranchStockUpdate
from app.services.stock_service import stock_service

router = APIRouter(prefix="/branches", tags=["stock"])



@router.get("/{branch_id}/stock", response_model=list[BranchStockRead])
async def list_stock(branch_id: int, session: SessionDep, user: ManagerDep):
    return await stock_service.list(session, branch_id, user)


@router.get("/{branch_id}/stock/critical", response_model=list[BranchStockRead])
async def list_critical_stock(branch_id: int, session: SessionDep, user: ManagerDep):
    return await stock_service.list_critical(session, branch_id, user)


@router.patch("/{branch_id}/stock/{ingredient_id}", response_model=BranchStockRead)
async def update_stock(
    branch_id: int,
    ingredient_id: int,
    data: BranchStockUpdate,
    session: SessionDep,
    user: ManagerDep,
):
    return await stock_service.upsert(session, branch_id, ingredient_id, data, user)
