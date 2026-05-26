from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, ManagerDep, SessionDep, WaiterDep
from app.schemas.coupon import CouponCreate, CouponRead, CouponUpdate
from app.services.coupon_service import coupon_service

router = APIRouter(prefix="/branches/{branch_id}/coupons", tags=["coupons"])


@router.get("", response_model=list[CouponRead])
async def list_coupons(branch_id: int, session: SessionDep, user: WaiterDep):
    return await coupon_service.list(session, branch_id, user)


@router.get("/validate", response_model=CouponRead)
async def validate_coupon(
    branch_id: int,
    session: SessionDep,
    user: WaiterDep,
    code: str = Query(..., description="The coupon code to validate"),
    order_total: float = Query(..., description="The current total of the order"),
):
    return await coupon_service.validate(session, branch_id, code, order_total, user)


@router.post("", response_model=CouponRead, status_code=201)
async def create_coupon(
    branch_id: int, data: CouponCreate, session: SessionDep, user: ManagerDep
):
    return await coupon_service.create(session, branch_id, data, user)


@router.get("/{coupon_id}", response_model=CouponRead)
async def get_coupon(
    branch_id: int, coupon_id: int, session: SessionDep, user: WaiterDep
):
    return await coupon_service.get(session, branch_id, coupon_id, user)


@router.patch("/{coupon_id}", response_model=CouponRead)
async def update_coupon(
    branch_id: int,
    coupon_id: int,
    data: CouponUpdate,
    session: SessionDep,
    user: ManagerDep,
):
    return await coupon_service.update(session, branch_id, coupon_id, data, user)


@router.delete("/{coupon_id}", status_code=204)
async def delete_coupon(
    branch_id: int, coupon_id: int, session: SessionDep, user: ManagerDep
):
    await coupon_service.delete(session, branch_id, coupon_id, user)
