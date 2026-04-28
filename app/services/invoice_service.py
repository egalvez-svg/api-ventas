from typing import Any, Dict
from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.inventory import Product
from app.models.sales import Order, OrderItem, OrderItemExtra


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

        return {
            "order_id": order.id,
            "branch_id": order.branch_id,
            "created_at": order.created_at,
            "total": order.total,
            "items": invoice_items
        }


invoice_service = InvoiceService()
