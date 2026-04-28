from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.base import User
from app.models.sales import Table
from app.schemas.sales import TableCreate, TableRead, TableUpdate


class TableService:
    def _assert_branch_access(self, user: User, branch_id: int) -> None:
        if user.role != "admin" and user.branch_id != branch_id:
            raise HTTPException(status_code=403, detail="Access denied for this branch")

    async def list(self, session: AsyncSession, branch_id: int, user: User) -> list[TableRead]:
        self._assert_branch_access(user, branch_id)
        result = await session.exec(select(Table).where(Table.branch_id == branch_id))
        return [TableRead.model_validate(t) for t in result.all()]

    async def create(
        self, session: AsyncSession, branch_id: int, data: TableCreate, user: User
    ) -> TableRead:
        self._assert_branch_access(user, branch_id)
        table = Table(branch_id=branch_id, **data.model_dump())
        session.add(table)
        await session.commit()
        await session.refresh(table)
        return TableRead.model_validate(table)

    async def update(
        self,
        session: AsyncSession,
        branch_id: int,
        table_id: int,
        data: TableUpdate,
        user: User,
    ) -> TableRead:
        self._assert_branch_access(user, branch_id)
        table = await session.get(Table, table_id)
        if not table or table.branch_id != branch_id:
            raise HTTPException(status_code=404, detail="Table not found")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(table, key, value)
        session.add(table)
        await session.commit()
        await session.refresh(table)
        return TableRead.model_validate(table)

    async def delete(
        self, session: AsyncSession, branch_id: int, table_id: int, user: User
    ) -> None:
        self._assert_branch_access(user, branch_id)
        table = await session.get(Table, table_id)
        if not table or table.branch_id != branch_id:
            raise HTTPException(status_code=404, detail="Table not found")
        await session.delete(table)
        await session.commit()


table_service = TableService()
