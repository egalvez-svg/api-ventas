from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import AdminDep, CurrentUser, SessionDep
from app.schemas.inventory import (
    ProductCreate,
    ProductRead,
    ProductReadWithRecipe,
    ProductUpdate,
    RecipeItemCreate,
    RecipeItemRead,
)
from app.services.product_service import product_service

router = APIRouter(prefix="/products", tags=["products"])



@router.get("/", response_model=list[ProductRead])
async def list_products(
    session: SessionDep,
    _: CurrentUser,
    category_id: Optional[int] = Query(default=None),
    active_only: bool = Query(default=True),
):
    return await product_service.list(session, category_id=category_id, active_only=active_only)


@router.post("/", response_model=ProductRead, status_code=201)
async def create_product(data: ProductCreate, session: SessionDep, _: AdminDep):
    return await product_service.create(session, data)


@router.get("/{product_id}", response_model=ProductReadWithRecipe)
async def get_product(product_id: int, session: SessionDep, _: CurrentUser):
    return await product_service.get_with_recipe(session, product_id)


@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(product_id: int, data: ProductUpdate, session: SessionDep, _: AdminDep):
    return await product_service.update(session, product_id, data)


@router.delete("/{product_id}", status_code=204)
async def deactivate_product(product_id: int, session: SessionDep, _: AdminDep):
    await product_service.delete(session, product_id)


@router.put("/{product_id}/recipe", response_model=list[RecipeItemRead])
async def set_recipe(
    product_id: int,
    items: list[RecipeItemCreate],
    session: SessionDep,
    _: AdminDep,
):
    return await product_service.set_recipe(session, product_id, items)
