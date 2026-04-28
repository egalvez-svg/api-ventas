from __future__ import annotations
from typing import Optional

from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.inventory import Category, Ingredient, Product, Recipe
from app.schemas.inventory import (
    ProductCreate,
    ProductReadWithRecipe,
    ProductUpdate,
    RecipeItemCreate,
    RecipeItemRead,
)
from app.services.base import CRUDBase


class ProductService(CRUDBase[Product, ProductCreate, ProductUpdate]):
    async def _assert_category_exists(self, session: AsyncSession, category_id: int) -> None:
        if not await session.get(Category, category_id):
            raise HTTPException(status_code=400, detail="Category not found")

    async def _load_recipe(self, session: AsyncSession, product_id: int) -> list[RecipeItemRead]:
        result = await session.exec(select(Recipe).where(Recipe.product_id == product_id))
        items = []
        for recipe in result.all():
            ingredient = await session.get(Ingredient, recipe.ingredient_id)
            items.append(
                RecipeItemRead(
                    ingredient_id=recipe.ingredient_id,
                    ingredient_name=ingredient.name,
                    unit=ingredient.unit,
                    quantity=recipe.quantity,
                )
            )
        return items

    async def list(  # type: ignore[override]
        self,
        session: AsyncSession,
        category_id: Optional[int] = None,
        active_only: bool = True,
    ) -> list[Product]:
        stmt = select(Product)
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
        if active_only:
            stmt = stmt.where(Product.is_active == True)  # noqa: E712
        return (await session.exec(stmt)).all()

    async def create(self, session: AsyncSession, data: ProductCreate) -> Product:
        await self._assert_category_exists(session, data.category_id)
        return await super().create(session, data)

    async def update(self, session: AsyncSession, id: int, data: ProductUpdate) -> Product:
        if data.category_id is not None:
            await self._assert_category_exists(session, data.category_id)
        return await super().update(session, id, data)

    async def delete(self, session: AsyncSession, id: int) -> None:
        """Soft-delete: marks as inactive instead of removing the row."""
        product = await self.get(session, id)
        product.is_active = False
        session.add(product)
        await session.commit()

    async def get_with_recipe(self, session: AsyncSession, id: int) -> ProductReadWithRecipe:
        product = await self.get(session, id)
        recipe = await self._load_recipe(session, id)
        return ProductReadWithRecipe(**product.model_dump(), recipe=recipe)

    async def set_recipe(
        self, session: AsyncSession, product_id: int, items: list[RecipeItemCreate]
    ) -> list[RecipeItemRead]:
        """Replace the full recipe for a product (all-or-nothing)."""
        await self.get(session, product_id)  # raises 404 if missing

        for item in items:
            if not await session.get(Ingredient, item.ingredient_id):
                raise HTTPException(
                    status_code=400,
                    detail=f"Ingredient {item.ingredient_id} not found",
                )

        existing = await session.exec(select(Recipe).where(Recipe.product_id == product_id))
        for row in existing.all():
            await session.delete(row)

        for item in items:
            session.add(
                Recipe(
                    product_id=product_id,
                    ingredient_id=item.ingredient_id,
                    quantity=item.quantity,
                )
            )

        await session.commit()
        return await self._load_recipe(session, product_id)


product_service = ProductService(Product)
