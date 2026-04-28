from __future__ import annotations
from typing import Generic, TypeVar

from fastapi import HTTPException
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateType = TypeVar("CreateType", bound=SQLModel)
UpdateType = TypeVar("UpdateType", bound=SQLModel)


class CRUDBase(Generic[ModelType, CreateType, UpdateType]):
    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    async def get(self, session: AsyncSession, id: int) -> ModelType:
        obj = await session.get(self.model, id)
        if not obj:
            raise HTTPException(status_code=404, detail=f"{self.model.__name__} not found")
        return obj

    async def list(self, session: AsyncSession) -> list[ModelType]:
        result = await session.exec(select(self.model))
        return result.all()

    async def create(self, session: AsyncSession, data: CreateType) -> ModelType:
        obj = self.model.model_validate(data)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def update(self, session: AsyncSession, id: int, data: UpdateType) -> ModelType:
        obj = await self.get(session, id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def delete(self, session: AsyncSession, id: int) -> None:
        obj = await self.get(session, id)
        await session.delete(obj)
        await session.commit()
