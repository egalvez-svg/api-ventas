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
    async def _assert_category_in_branch(self, session: AsyncSession, category_id: int, branch_id: int) -> None:
        category = await session.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=400, detail="Categoría no encontrada")
        if category.branch_id != branch_id:
            raise HTTPException(status_code=400, detail="La categoría no pertenece a este local")

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

    async def get_in_branch(self, session: AsyncSession, id: int, branch_id: int) -> Product:
        obj = await self.get(session, id)
        if obj.branch_id != branch_id:
            raise HTTPException(status_code=404, detail="Product not found")
        return obj

    async def list(  # type: ignore[override]
        self,
        session: AsyncSession,
        branch_id: int,
        category_id: Optional[int] = None,
        active_only: bool = True,
    ) -> list[Product]:
        stmt = select(Product).where(Product.branch_id == branch_id)
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
        if active_only:
            stmt = stmt.where(Product.is_active == True)  # noqa: E712
        return list((await session.exec(stmt)).all())

    async def create(self, session: AsyncSession, data: ProductCreate, branch_id: int) -> Product:  # type: ignore[override]
        await self._assert_category_in_branch(session, data.category_id, branch_id)
        obj = Product(branch_id=branch_id, **data.model_dump())
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def update(self, session: AsyncSession, id: int, data: ProductUpdate, branch_id: int) -> Product:  # type: ignore[override]
        obj = await self.get_in_branch(session, id, branch_id)
        if data.category_id is not None:
            await self._assert_category_in_branch(session, data.category_id, branch_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def delete(self, session: AsyncSession, id: int, branch_id: int) -> None:  # type: ignore[override]
        product = await self.get_in_branch(session, id, branch_id)
        product.is_active = False
        session.add(product)
        await session.commit()

    async def get_with_recipe(self, session: AsyncSession, id: int, branch_id: int) -> ProductReadWithRecipe:
        product = await self.get_in_branch(session, id, branch_id)
        recipe = await self._load_recipe(session, id)
        return ProductReadWithRecipe(**product.model_dump(), recipe=recipe)

    async def set_recipe(
        self, session: AsyncSession, product_id: int, items: list[RecipeItemCreate], branch_id: int
    ) -> list[RecipeItemRead]:
        """Replace the full recipe for a product (all-or-nothing)."""
        await self.get_in_branch(session, product_id, branch_id)

        for item in items:
            ingredient = await session.get(Ingredient, item.ingredient_id)
            if not ingredient:
                raise HTTPException(status_code=400, detail=f"Ingrediente {item.ingredient_id} no encontrado")
            if ingredient.branch_id != branch_id:
                raise HTTPException(status_code=400, detail=f"Ingrediente {item.ingredient_id} no pertenece a este local")

        existing = await session.exec(select(Recipe).where(Recipe.product_id == product_id))
        for row in existing.all():
            await session.delete(row)

        for item in items:
            session.add(Recipe(product_id=product_id, ingredient_id=item.ingredient_id, quantity=item.quantity))

        await session.commit()
        return await self._load_recipe(session, product_id)


product_service = ProductService(Product)
