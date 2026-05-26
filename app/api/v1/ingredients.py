from fastapi import APIRouter

from app.core.deps import CurrentUser, ManagerDep, SessionDep
from app.schemas.inventory import IngredientCreate, IngredientRead, IngredientUpdate
from app.services.ingredient_service import ingredient_service

router = APIRouter(prefix="/branches/{branch_id}/ingredients", tags=["ingredients"])


@router.get("/", response_model=list[IngredientRead])
async def list_ingredients(branch_id: int, session: SessionDep, _: CurrentUser):
    return await ingredient_service.list(session, branch_id)


@router.post("/", response_model=IngredientRead, status_code=201)
async def create_ingredient(branch_id: int, data: IngredientCreate, session: SessionDep, _: ManagerDep):
    return await ingredient_service.create(session, data, branch_id)


@router.get("/{ingredient_id}", response_model=IngredientRead)
async def get_ingredient(branch_id: int, ingredient_id: int, session: SessionDep, _: CurrentUser):
    return await ingredient_service.get_in_branch(session, ingredient_id, branch_id)


@router.patch("/{ingredient_id}", response_model=IngredientRead)
async def update_ingredient(branch_id: int, ingredient_id: int, data: IngredientUpdate, session: SessionDep, _: ManagerDep):
    return await ingredient_service.update(session, ingredient_id, data, branch_id)


@router.delete("/{ingredient_id}", status_code=204)
async def delete_ingredient(branch_id: int, ingredient_id: int, session: SessionDep, _: ManagerDep):
    await ingredient_service.delete(session, ingredient_id, branch_id)
