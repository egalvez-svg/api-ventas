from __future__ import annotations
from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.base import User
from app.models.inventory import Product
from app.models.sales import Order, OrderItem, OrderItemExtra, Table
from app.schemas.sales import (
    OrderCreate,
    OrderItemExtraRead,
    OrderItemRead,
    OrderRead,
    OrderStatusUpdate,
    TableInvoiceRead,
)
from app.services.stock_service import stock_service

_VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"cooking", "cancelled"},
    "cooking": {"served", "delivered", "cancelled"},
    "served": {"delivered", "paid", "cancelled"},
    "delivered": {"paid", "cancelled"},
    "paid": set(),
    "cancelled": set(),
}


class OrderService:
    def _assert_branch_access(self, user: User, branch_id: int) -> None:
        if user.role != "admin" and user.branch_id != branch_id:
            raise HTTPException(status_code=403, detail="Access denied for this branch")

    async def _build_read(self, session: AsyncSession, order: Order) -> OrderRead:
        items_result = await session.exec(
            select(OrderItem).where(OrderItem.order_id == order.id)
        )
        item_reads: list[OrderItemRead] = []
        for item in items_result.all():
            extras_result = await session.exec(
                select(OrderItemExtra).where(OrderItemExtra.order_item_id == item.id)
            )
            extras = [
                OrderItemExtraRead(ingredient_id=e.ingredient_id, quantity=e.quantity)
                for e in extras_result.all()
            ]
            product = await session.get(Product, item.product_id)
            item_reads.append(
                OrderItemRead(
                    id=item.id,
                    product_id=item.product_id,
                    product_name=product.name if product else "—",
                    quantity=item.quantity,
                    price=item.price,
                    notes=item.notes,
                    extras=extras,
                )
            )
        waiter = await session.get(User, order.user_id)
        return OrderRead(
            id=order.id,
            branch_id=order.branch_id,
            table_id=order.table_id,
            user_id=order.user_id,
            waiter_name=waiter.full_name if waiter else "—",
            status=order.status,
            total=order.total,
            discount=order.discount,
            coupon_id=order.coupon_id,
            tip=order.tip,
            created_at=order.created_at,
            items=item_reads,
        )

    async def list_by_shift(
        self,
        session: AsyncSession,
        branch_id: int,
        shift_id: int,
        user: User,
    ) -> list[OrderRead]:
        self._assert_branch_access(user, branch_id)
        result = await session.exec(
            select(Order)
            .where(Order.branch_id == branch_id, Order.shift_id == shift_id)
            .order_by(Order.created_at.desc())
        )
        return [await self._build_read(session, o) for o in result.all()]

    async def list(
        self,
        session: AsyncSession,
        branch_id: int,
        user: User,
        status: str | None = None,
    ) -> list[OrderRead]:
        self._assert_branch_access(user, branch_id)
        q = select(Order).where(Order.branch_id == branch_id)
        if status:
            q = q.where(Order.status == status)
        result = await session.exec(q.order_by(Order.created_at.desc()))
        return [await self._build_read(session, o) for o in result.all()]

    async def get(
        self, session: AsyncSession, branch_id: int, order_id: int, user: User
    ) -> OrderRead:
        self._assert_branch_access(user, branch_id)
        order = await session.get(Order, order_id)
        if not order or order.branch_id != branch_id:
            raise HTTPException(status_code=404, detail="Order not found")
        return await self._build_read(session, order)

    async def create(
        self, session: AsyncSession, branch_id: int, data: OrderCreate, user: User
    ) -> OrderRead:
        self._assert_branch_access(user, branch_id)
        if not data.items:
            raise HTTPException(status_code=422, detail="Order must have at least one item")

        product_prices: dict[int, float] = {}
        total = 0.0
        for item_data in data.items:
            product = await session.get(Product, item_data.product_id)
            if not product or not product.is_active:
                raise HTTPException(
                    status_code=404, detail=f"Product {item_data.product_id} not found"
                )
            product_prices[item_data.product_id] = product.price
            total += product.price * item_data.quantity

        from app.services.shift_service import get_active_shift
        shift = await get_active_shift(branch_id, session)
        if not shift:
            raise HTTPException(
                status_code=400, detail="No active shift found for this branch. Please open a shift first."
            )

        discount = 0.0
        coupon_id = None
        if data.coupon_code:
            from app.services.coupon_service import coupon_service
            coupon = await coupon_service.validate(session, branch_id, data.coupon_code, total, user)
            coupon_id = coupon.id
            if coupon.discount_type == "percentage":
                discount = total * (coupon.discount_value / 100.0)
            else:
                discount = coupon.discount_value
            discount = min(discount, total)
            total = total - discount

        order = Order(
            branch_id=branch_id,
            table_id=data.table_id,
            user_id=user.id,
            shift_id=shift.id,
            coupon_id=coupon_id,
            discount=discount,
            total=total,
        )
        session.add(order)
        await session.flush()

        for item_data in data.items:
            item = OrderItem(
                order_id=order.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                price=product_prices[item_data.product_id],
                notes=item_data.notes,
            )
            session.add(item)
            await session.flush()

            for extra in item_data.extras:
                session.add(
                    OrderItemExtra(
                        order_item_id=item.id,
                        ingredient_id=extra.ingredient_id,
                        quantity=extra.quantity,
                    )
                )

        if data.table_id:
            table = await session.get(Table, data.table_id)
            if table and table.branch_id == branch_id:
                table.status = "occupied"
                session.add(table)

        await session.commit()
        await session.refresh(order)
        return await self._build_read(session, order)

    async def update_status(
        self,
        session: AsyncSession,
        branch_id: int,
        order_id: int,
        data: OrderStatusUpdate,
        user: User,
    ) -> OrderRead:
        self._assert_branch_access(user, branch_id)
        order = await session.get(Order, order_id)
        if not order or order.branch_id != branch_id:
            raise HTTPException(status_code=404, detail="Order not found")

        allowed = _VALID_TRANSITIONS.get(order.status, set())
        if data.status not in allowed:
            raise HTTPException(
                status_code=422,
                detail=f"Cannot transition from '{order.status}' to '{data.status}'",
            )

        order.status = data.status
        if data.status == "paid":
            order.tip = data.tip
            if data.coupon_code and not order.coupon_id:
                from app.services.coupon_service import coupon_service
                from app.models.sales import Coupon
                base_total = order.total + order.discount  # total sin descuento previo
                coupon = await coupon_service.validate(session, branch_id, data.coupon_code, base_total, user)
                if coupon.discount_type == "percentage":
                    discount = base_total * (coupon.discount_value / 100.0)
                else:
                    discount = coupon.discount_value
                discount = min(discount, base_total)
                order.coupon_id = coupon.id
                order.discount = discount
                order.total = base_total - discount
                coupon.used_count += 1
                session.add(coupon)
            elif order.coupon_id:
                from app.models.sales import Coupon
                coupon = await session.get(Coupon, order.coupon_id)
                if coupon:
                    coupon.used_count += 1
                    session.add(coupon)
        session.add(order)
        await session.flush()

        if data.status == "paid":
            items_result = await session.exec(
                select(OrderItem).where(OrderItem.order_id == order.id)
            )
            items = items_result.all()
            all_extras: list[OrderItemExtra] = []
            for item in items:
                extras_result = await session.exec(
                    select(OrderItemExtra).where(OrderItemExtra.order_item_id == item.id)
                )
                all_extras.extend(extras_result.all())
            await stock_service.deduct_order_stock(session, branch_id, items, all_extras)

        if data.status in ("paid", "cancelled") and order.table_id:
            remaining = await session.exec(
                select(Order).where(
                    Order.table_id == order.table_id,
                    Order.id != order.id,
                    Order.status.in_(["pending", "cooking", "served", "delivered"]),
                )
            )
            if not remaining.first():
                table = await session.get(Table, order.table_id)
                if table:
                    table.status = "available"
                    session.add(table)

        await session.commit()
        await session.refresh(order)
        return await self._build_read(session, order)


    async def pay_table_orders(
        self,
        session: AsyncSession,
        branch_id: int,
        table_id: int,
        tip: float,
        user: User,
    ) -> TableInvoiceRead:
        self._assert_branch_access(user, branch_id)

        table = await session.get(Table, table_id)
        if not table or table.branch_id != branch_id:
            raise HTTPException(status_code=404, detail="Table not found")

        result = await session.exec(
            select(Order).where(
                Order.table_id == table_id,
                Order.branch_id == branch_id,
                Order.status.in_(["pending", "cooking", "served", "delivered"]),
            )
        )
        orders = result.all()

        if not orders:
            raise HTTPException(status_code=422, detail="No active orders for this table")

        for i, order in enumerate(orders):
            order.status = "paid"
            if i == 0:
                order.tip = tip
            if order.coupon_id:
                from app.models.sales import Coupon
                coupon = await session.get(Coupon, order.coupon_id)
                if coupon:
                    coupon.used_count += 1
                    session.add(coupon)
            session.add(order)

            items_result = await session.exec(
                select(OrderItem).where(OrderItem.order_id == order.id)
            )
            items = items_result.all()
            all_extras: list[OrderItemExtra] = []
            for item in items:
                extras_result = await session.exec(
                    select(OrderItemExtra).where(OrderItemExtra.order_item_id == item.id)
                )
                all_extras.extend(extras_result.all())
            await stock_service.deduct_order_stock(session, branch_id, items, all_extras)

        table.status = "available"
        session.add(table)
        await session.commit()

        for order in orders:
            await session.refresh(order)

        order_reads = [await self._build_read(session, o) for o in orders]
        subtotal = sum(o.total for o in orders)
        return TableInvoiceRead(
            table_id=table_id,
            branch_id=branch_id,
            orders=order_reads,
            subtotal=subtotal,
            tip=tip,
            total=subtotal + tip,
        )


order_service = OrderService()
