from __future__ import annotations
from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.inventory import Category
from app.schemas.inventory import CategoryCreate, CategoryUpdate
from app.services.base import CRUDBase


class CategoryService(CRUDBase[Category, CategoryCreate, CategoryUpdate]):
    async def _assert_unique_name(
        self, session: AsyncSession, name: str, exclude_id: int | None = None
    ) -> None:
        stmt = select(Category).where(Category.name == name)
        if exclude_id is not None:
            stmt = stmt.where(Category.id != exclude_id)
        if (await session.exec(stmt)).first():
            raise HTTPException(status_code=400, detail="Category name already exists")

    async def create(self, session: AsyncSession, data: CategoryCreate) -> Category:
        await self._assert_unique_name(session, data.name)
        return await super().create(session, data)

    async def update(self, session: AsyncSession, id: int, data: CategoryUpdate) -> Category:
        if data.name:
            await self._assert_unique_name(session, data.name, exclude_id=id)
        return await super().update(session, id, data)


category_service = CategoryService(Category)
