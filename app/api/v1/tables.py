from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import AdminDep, CurrentUser, ManagerDep, SessionDep
from app.schemas.sales import TableCreate, TableRead, TableUpdate
from app.services.table_service import table_service

router = APIRouter(prefix="/branches/{branch_id}/tables", tags=["tables"])



@router.get("", response_model=list[TableRead])
async def list_tables(branch_id: int, session: SessionDep, user: CurrentUser):
    return await table_service.list(session, branch_id, user)


@router.post("", response_model=TableRead, status_code=201)
async def create_table(
    branch_id: int, data: TableCreate, session: SessionDep, user: ManagerDep
):
    return await table_service.create(session, branch_id, data, user)


@router.patch("/{table_id}", response_model=TableRead)
async def update_table(
    branch_id: int,
    table_id: int,
    data: TableUpdate,
    session: SessionDep,
    user: ManagerDep,
):
    return await table_service.update(session, branch_id, table_id, data, user)


@router.delete("/{table_id}", status_code=204)
async def delete_table(
    branch_id: int, table_id: int, session: SessionDep, user: AdminDep
):
    await table_service.delete(session, branch_id, table_id, user)
