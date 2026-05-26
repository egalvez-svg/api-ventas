from __future__ import annotations
from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.deps import AuthContext
from app.models.inventory import BranchStock, Ingredient, Recipe
from app.models.sales import OrderItem, OrderItemExtra
from app.schemas.inventory import BranchStockRead, BranchStockUpdate


class StockService:
    def _assert_branch_access(self, user: AuthContext, branch_id: int) -> None:
        if user.role != "admin" and user.branch_id != branch_id:
            raise HTTPException(status_code=403, detail="Access denied for this branch")

    async def _to_read(self, session: AsyncSession, stock: BranchStock) -> BranchStockRead:
        ingredient = await session.get(Ingredient, stock.ingredient_id)
        return BranchStockRead(
            branch_id=stock.branch_id,
            ingredient_id=stock.ingredient_id,
            ingredient_name=ingredient.name,
            unit=ingredient.unit,
            quantity=stock.quantity,
            min_stock=stock.min_stock,
            is_critical=stock.quantity <= stock.min_stock,
        )

    async def list(
        self, session: AsyncSession, branch_id: int, user: AuthContext
    ) -> list[BranchStockRead]:
        self._assert_branch_access(user, branch_id)
        result = await session.exec(
            select(BranchStock).where(BranchStock.branch_id == branch_id)
        )
        return [await self._to_read(session, s) for s in result.all()]

    async def list_critical(
        self, session: AsyncSession, branch_id: int, user: AuthContext
    ) -> list[BranchStockRead]:
        items = await self.list(session, branch_id, user)
        return [item for item in items if item.is_critical]

    async def upsert(
        self,
        session: AsyncSession,
        branch_id: int,
        ingredient_id: int,
        data: BranchStockUpdate,
        user: AuthContext,
    ) -> BranchStockRead:
        self._assert_branch_access(user, branch_id)

        stock = await session.get(BranchStock, (branch_id, ingredient_id))
        if not stock:
            ingredient = await session.get(Ingredient, ingredient_id)
            if not ingredient:
                raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
            if ingredient.branch_id != branch_id:
                raise HTTPException(status_code=400, detail="El ingrediente no pertenece a este local")
            stock = BranchStock(branch_id=branch_id, ingredient_id=ingredient_id)

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(stock, key, value)
        session.add(stock)
        await session.commit()
        await session.refresh(stock)
        return await self._to_read(session, stock)

    async def deduct_order_stock(
        self,
        session: AsyncSession,
        branch_id: int,
        order_items: list[OrderItem],
        extras: list[OrderItemExtra] | None = None,
    ) -> None:
        """Decrements BranchStock via recipes for order items, and directly for extras."""
        for item in order_items:
            result = await session.exec(
                select(Recipe).where(Recipe.product_id == item.product_id)
            )
            for recipe in result.all():
                stock = await session.get(BranchStock, (branch_id, recipe.ingredient_id))
                if stock:
                    stock.quantity -= item.quantity * recipe.quantity
                    session.add(stock)

        if extras:
            for extra in extras:
                stock = await session.get(BranchStock, (branch_id, extra.ingredient_id))
                if stock:
                    stock.quantity -= extra.quantity
                    session.add(stock)


stock_service = StockService()
