from typing import Any, Dict
from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.inventory import Product
from app.models.sales import Order, OrderItem, OrderItemExtra, Table


class InvoiceService:
    async def generate_pre_boleta(self, session: AsyncSession, order_id: int) -> Dict[str, Any]:
        order = await session.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        items_result = await session.exec(
            select(OrderItem).where(OrderItem.order_id == order.id)
        )
        items = items_result.all()

        invoice_items = []
        for item in items:
            product = await session.get(Product, item.product_id)
            
            extras_result = await session.exec(
                select(OrderItemExtra).where(OrderItemExtra.order_item_id == item.id)
            )
            extras = extras_result.all()

            invoice_items.append({
                "product_name": product.name if product else "Unknown",
                "quantity": item.quantity,
                "price": item.price,
                "subtotal": item.quantity * item.price,
                "extras": [{"ingredient_id": e.ingredient_id, "quantity": e.quantity} for e in extras]
            })

        subtotal = sum(i["subtotal"] for i in invoice_items)
        return {
            "order_id": order.id,
            "branch_id": order.branch_id,
            "created_at": order.created_at,
            "subtotal": subtotal,
            "discount": order.discount,
            "coupon_id": order.coupon_id,
            "tip": order.tip,
            "total": order.total + order.tip,
            "items": invoice_items,
        }

    async def generate_table_invoice(
        self, session: AsyncSession, branch_id: int, table_id: int
    ) -> Dict[str, Any]:
        table = await session.get(Table, table_id)
        if not table or table.branch_id != branch_id:
            raise HTTPException(status_code=404, detail="Table not found")

        result = await session.exec(
            select(Order).where(
                Order.table_id == table_id,
                Order.branch_id == branch_id,
                Order.status.in_(["pending", "cooking", "served"]),
            )
        )
        orders = result.all()

        if not orders:
            raise HTTPException(status_code=404, detail="No active orders for this table")

        order_summaries = []
        subtotal = 0.0
        discount = 0.0

        for order in orders:
            items_result = await session.exec(
                select(OrderItem).where(OrderItem.order_id == order.id)
            )
            items = items_result.all()

            invoice_items = []
            for item in items:
                product = await session.get(Product, item.product_id)
                extras_result = await session.exec(
                    select(OrderItemExtra).where(OrderItemExtra.order_item_id == item.id)
                )
                extras = extras_result.all()
                invoice_items.append({
                    "product_name": product.name if product else "Unknown",
                    "quantity": item.quantity,
                    "price": item.price,
                    "subtotal": item.quantity * item.price,
                    "extras": [{"ingredient_id": e.ingredient_id, "quantity": e.quantity} for e in extras],
                })

            order_subtotal = sum(i["subtotal"] for i in invoice_items)
            order_summaries.append({
                "order_id": order.id,
                "status": order.status,
                "created_at": order.created_at,
                "items": invoice_items,
                "order_subtotal": order_subtotal,
                "discount": order.discount,
                "order_total": order.total,
            })
            subtotal += order_subtotal
            discount += order.discount

        return {
            "table_id": table_id,
            "branch_id": branch_id,
            "orders": order_summaries,
            "subtotal": subtotal,
            "discount": discount,
            "tip": 0.0,
            "total": subtotal - discount,
        }


invoice_service = InvoiceService()
