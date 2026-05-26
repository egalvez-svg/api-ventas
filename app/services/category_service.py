from __future__ import annotations
from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.inventory import Category
from app.schemas.inventory import CategoryCreate, CategoryUpdate
from app.services.base import CRUDBase


class CategoryService(CRUDBase[Category, CategoryCreate, CategoryUpdate]):
    async def _assert_unique_name(
        self, session: AsyncSession, name: str, branch_id: int, exclude_id: int | None = None
    ) -> None:
        stmt = select(Category).where(Category.name == name, Category.branch_id == branch_id)
        if exclude_id is not None:
            stmt = stmt.where(Category.id != exclude_id)
        if (await session.exec(stmt)).first():
            raise HTTPException(status_code=400, detail="Ya existe una categoría con ese nombre en este local")

    async def get_in_branch(self, session: AsyncSession, id: int, branch_id: int) -> Category:
        obj = await self.get(session, id)
        if obj.branch_id != branch_id:
            raise HTTPException(status_code=404, detail="Category not found")
        return obj

    async def list(self, session: AsyncSession, branch_id: int) -> list[Category]:  # type: ignore[override]
        result = await session.exec(select(Category).where(Category.branch_id == branch_id))
        return list(result.all())

    async def create(self, session: AsyncSession, data: CategoryCreate, branch_id: int) -> Category:  # type: ignore[override]
        await self._assert_unique_name(session, data.name, branch_id)
        obj = Category(branch_id=branch_id, **data.model_dump())
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def update(self, session: AsyncSession, id: int, data: CategoryUpdate, branch_id: int) -> Category:  # type: ignore[override]
        obj = await self.get_in_branch(session, id, branch_id)
        if data.name:
            await self._assert_unique_name(session, data.name, branch_id, exclude_id=id)
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


category_service = CategoryService(Category)
