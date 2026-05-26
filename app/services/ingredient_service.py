from __future__ import annotations
from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.inventory import Ingredient
from app.schemas.inventory import IngredientCreate, IngredientUpdate
from app.services.base import CRUDBase


class IngredientService(CRUDBase[Ingredient, IngredientCreate, IngredientUpdate]):
    async def get_in_branch(self, session: AsyncSession, id: int, branch_id: int) -> Ingredient:
        obj = await self.get(session, id)
        if obj.branch_id != branch_id:
            raise HTTPException(status_code=404, detail="Ingredient not found")
        return obj

    async def list(self, session: AsyncSession, branch_id: int) -> list[Ingredient]:  # type: ignore[override]
        result = await session.exec(select(Ingredient).where(Ingredient.branch_id == branch_id))
        return list(result.all())

    async def create(self, session: AsyncSession, data: IngredientCreate, branch_id: int) -> Ingredient:  # type: ignore[override]
        obj = Ingredient(branch_id=branch_id, **data.model_dump())
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def update(self, session: AsyncSession, id: int, data: IngredientUpdate, branch_id: int) -> Ingredient:  # type: ignore[override]
        obj = await self.get_in_branch(session, id, branch_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def delete(self, session: AsyncSession, id: int, branch_id: int) -> None:  # type: ignore[override]
        obj = await self.get_in_branch(session, id, branch_id)
        await session.delete(obj)
        await session.commit()


ingredient_service = IngredientService(Ingredient)
