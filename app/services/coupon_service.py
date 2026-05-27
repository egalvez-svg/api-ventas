from datetime import datetime
from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.base import User
from app.models.sales import Coupon
from app.schemas.coupon import CouponCreate, CouponUpdate


class CouponService:
    def _assert_branch_access(self, user: User, branch_id: int) -> None:
        if user.role != "admin" and user.branch_id != branch_id:
            raise HTTPException(status_code=403, detail="Access denied for this branch")

    async def list(self, session: AsyncSession, branch_id: int, user: User) -> list[Coupon]:
        self._assert_branch_access(user, branch_id)
        # Return coupons for this branch, or global coupons (branch_id is null)
        q = select(Coupon).where(
            (Coupon.branch_id == branch_id) | (Coupon.branch_id == None)
        )
        result = await session.exec(q.order_by(Coupon.created_at.desc()))
        return list(result.all())

    async def get(self, session: AsyncSession, branch_id: int, coupon_id: int, user: User) -> Coupon:
        self._assert_branch_access(user, branch_id)
        coupon = await session.get(Coupon, coupon_id)
        if not coupon or (coupon.branch_id is not None and coupon.branch_id != branch_id):
            raise HTTPException(status_code=404, detail="Coupon not found")
        return coupon

    async def create(self, session: AsyncSession, branch_id: int, data: CouponCreate, user: User) -> Coupon:
        self._assert_branch_access(user, branch_id)
        
        # Enforce code upper-casing and trimming
        code_upper = data.code.strip().upper()
        if not code_upper:
            raise HTTPException(status_code=400, detail="Coupon code cannot be empty")

        # Check if code already exists globally
        existing = await session.exec(select(Coupon).where(Coupon.code == code_upper))
        if existing.first():
            raise HTTPException(status_code=400, detail="Coupon code already exists")

        if data.discount_type not in ("percentage", "fixed"):
            raise HTTPException(status_code=400, detail="Discount type must be 'percentage' or 'fixed'")

        if data.discount_value <= 0:
            raise HTTPException(status_code=400, detail="Discount value must be greater than zero")

        exp = data.expiration_date
        if exp is not None and exp.tzinfo is not None:
            exp = exp.replace(tzinfo=None)

        coupon = Coupon(
            code=code_upper,
            description=data.description,
            discount_type=data.discount_type,
            discount_value=data.discount_value,
            min_order_value=data.min_order_value,
            expiration_date=exp,
            max_uses=data.max_uses,
            is_active=data.is_active,
            branch_id=branch_id,
        )
        session.add(coupon)
        await session.commit()
        await session.refresh(coupon)
        return coupon

    async def update(
        self, session: AsyncSession, branch_id: int, coupon_id: int, data: CouponUpdate, user: User
    ) -> Coupon:
        self._assert_branch_access(user, branch_id)
        coupon = await session.get(Coupon, coupon_id)
        if not coupon or (coupon.branch_id is not None and coupon.branch_id != branch_id):
            raise HTTPException(status_code=404, detail="Coupon not found")

        if data.code is not None:
            code_upper = data.code.strip().upper()
            if not code_upper:
                raise HTTPException(status_code=400, detail="Coupon code cannot be empty")
            if code_upper != coupon.code:
                existing = await session.exec(select(Coupon).where(Coupon.code == code_upper))
                if existing.first():
                    raise HTTPException(status_code=400, detail="Coupon code already exists")
                coupon.code = code_upper

        if data.description is not None:
            coupon.description = data.description
        
        if data.discount_type is not None:
            if data.discount_type not in ("percentage", "fixed"):
                raise HTTPException(status_code=400, detail="Discount type must be 'percentage' or 'fixed'")
            coupon.discount_type = data.discount_type
            
        if data.discount_value is not None:
            if data.discount_value <= 0:
                raise HTTPException(status_code=400, detail="Discount value must be greater than zero")
            coupon.discount_value = data.discount_value
            
        if data.min_order_value is not None:
            coupon.min_order_value = data.min_order_value
        if data.expiration_date is not None:
            exp = data.expiration_date
            if exp.tzinfo is not None:
                exp = exp.replace(tzinfo=None)
            coupon.expiration_date = exp
        if data.max_uses is not None:
            coupon.max_uses = data.max_uses
        if data.is_active is not None:
            coupon.is_active = data.is_active

        session.add(coupon)
        await session.commit()
        await session.refresh(coupon)
        return coupon

    async def delete(self, session: AsyncSession, branch_id: int, coupon_id: int, user: User) -> None:
        self._assert_branch_access(user, branch_id)
        coupon = await session.get(Coupon, coupon_id)
        if not coupon or (coupon.branch_id is not None and coupon.branch_id != branch_id):
            raise HTTPException(status_code=404, detail="Coupon not found")
        await session.delete(coupon)
        await session.commit()

    async def validate(
        self, session: AsyncSession, branch_id: int, code: str, order_total: float, user: User
    ) -> Coupon:
        self._assert_branch_access(user, branch_id)
        
        code_upper = code.strip().upper()
        q = select(Coupon).where(Coupon.code == code_upper)
        result = await session.exec(q)
        coupon = result.first()
        if not coupon:
            raise HTTPException(status_code=404, detail="Coupon not found")

        if not coupon.is_active:
            raise HTTPException(status_code=400, detail="Coupon is inactive")

        exp = coupon.expiration_date
        if exp is not None and exp.replace(tzinfo=None) < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Coupon has expired")

        if coupon.max_uses is not None and coupon.used_count >= coupon.max_uses:
            raise HTTPException(status_code=400, detail="Coupon usage limit reached")

        if coupon.branch_id is not None and coupon.branch_id != branch_id:
            raise HTTPException(status_code=400, detail="Coupon is not valid for this branch")

        if order_total < coupon.min_order_value:
            raise HTTPException(
                status_code=400,
                detail=f"Order total ({order_total}) is below the minimum required ({coupon.min_order_value}) for this coupon",
            )

        return coupon


coupon_service = CouponService()
