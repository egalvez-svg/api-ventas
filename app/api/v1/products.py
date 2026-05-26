from typing import Optional

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, ManagerDep, SessionDep
from app.schemas.inventory import (
    ProductCreate,
    ProductRead,
    ProductReadWithRecipe,
    ProductUpdate,
    RecipeItemCreate,
    RecipeItemRead,
)
from app.services.product_service import product_service

router = APIRouter(prefix="/branches/{branch_id}/products", tags=["products"])


@router.get("/", response_model=list[ProductRead])
async def list_products(
    branch_id: int,
    session: SessionDep,
    _: CurrentUser,
    category_id: Optional[int] = Query(default=None),
    active_only: bool = Query(default=True),
):
    return await product_service.list(session, branch_id, category_id=category_id, active_only=active_only)


@router.post("/", response_model=ProductRead, status_code=201)
async def create_product(branch_id: int, data: ProductCreate, session: SessionDep, _: ManagerDep):
    return await product_service.create(session, data, branch_id)


@router.get("/{product_id}", response_model=ProductReadWithRecipe)
async def get_product(branch_id: int, product_id: int, session: SessionDep, _: CurrentUser):
    return await product_service.get_with_recipe(session, product_id, branch_id)


@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(branch_id: int, product_id: int, data: ProductUpdate, session: SessionDep, _: ManagerDep):
    return await product_service.update(session, product_id, data, branch_id)


@router.delete("/{product_id}", status_code=204)
async def deactivate_product(branch_id: int, product_id: int, session: SessionDep, _: ManagerDep):
    await product_service.delete(session, product_id, branch_id)


@router.put("/{product_id}/recipe", response_model=list[RecipeItemRead])
async def set_recipe(
    branch_id: int,
    product_id: int,
    items: list[RecipeItemCreate],
    session: SessionDep,
    _: ManagerDep,
):
    return await product_service.set_recipe(session, product_id, items, branch_id)
