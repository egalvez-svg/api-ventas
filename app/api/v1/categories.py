from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import AdminDep, CurrentUser, SessionDep
from app.schemas.inventory import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.category_service import category_service

router = APIRouter(prefix="/categories", tags=["categories"])



@router.get("/", response_model=list[CategoryRead])
async def list_categories(session: SessionDep, _: CurrentUser):
    return await category_service.list(session)


@router.post("/", response_model=CategoryRead, status_code=201)
async def create_category(data: CategoryCreate, session: SessionDep, _: AdminDep):
    return await category_service.create(session, data)


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(category_id: int, session: SessionDep, _: CurrentUser):
    return await category_service.get(session, category_id)


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(category_id: int, data: CategoryUpdate, session: SessionDep, _: AdminDep):
    return await category_service.update(session, category_id, data)


@router.delete("/{category_id}", status_code=204)
async def delete_category(category_id: int, session: SessionDep, _: AdminDep):
    await category_service.delete(session, category_id)
