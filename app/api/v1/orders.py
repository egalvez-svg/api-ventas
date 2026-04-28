from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, KitchenDep, SessionDep, WaiterDep
from app.schemas.sales import OrderCreate, OrderRead, OrderStatusUpdate
from app.services.order_service import order_service

router = APIRouter(prefix="/branches/{branch_id}/orders", tags=["orders"])



@router.get("", response_model=list[OrderRead])
async def list_orders(
    branch_id: int,
    session: SessionDep,
    user: CurrentUser,
    status: Optional[str] = Query(default=None),
):
    return await order_service.list(session, branch_id, user, status)


@router.get("/kitchen", response_model=list[OrderRead])
async def kitchen_view(branch_id: int, session: SessionDep, user: KitchenDep):
    return await order_service.list(session, branch_id, user, status="cooking")


@router.post("", response_model=OrderRead, status_code=201)
async def create_order(
    branch_id: int, data: OrderCreate, session: SessionDep, user: WaiterDep
):
    return await order_service.create(session, branch_id, data, user)


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(branch_id: int, order_id: int, session: SessionDep, user: CurrentUser):
    return await order_service.get(session, branch_id, order_id, user)


@router.patch("/{order_id}/status", response_model=OrderRead)
async def update_order_status(
    branch_id: int,
    order_id: int,
    data: OrderStatusUpdate,
    session: SessionDep,
    user: CurrentUser,
):
    return await order_service.update_status(session, branch_id, order_id, data, user)


@router.get("/{order_id}/invoice", response_model=dict)
async def get_order_invoice(
    branch_id: int, order_id: int, session: SessionDep, user: CurrentUser
):
    from app.services.invoice_service import invoice_service
    # Basic check to ensure order belongs to branch
    order = await order_service.get(session, branch_id, order_id, user)
    return await invoice_service.generate_pre_boleta(session, order_id)
