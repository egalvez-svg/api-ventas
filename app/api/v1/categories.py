from fastapi import APIRouter

from app.core.deps import CurrentUser, ManagerDep, SessionDep
from app.schemas.inventory import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.category_service import category_service

router = APIRouter(prefix="/branches/{branch_id}/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryRead])
async def list_categories(branch_id: int, session: SessionDep, _: CurrentUser):
    return await category_service.list(session, branch_id)


@router.post("/", response_model=CategoryRead, status_code=201)
async def create_category(branch_id: int, data: CategoryCreate, session: SessionDep, _: ManagerDep):
    return await category_service.create(session, data, branch_id)


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(branch_id: int, category_id: int, session: SessionDep, _: CurrentUser):
    return await category_service.get_in_branch(session, category_id, branch_id)


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(branch_id: int, category_id: int, data: CategoryUpdate, session: SessionDep, _: ManagerDep):
    return await category_service.update(session, category_id, data, branch_id)


@router.delete("/{category_id}", status_code=204)
async def delete_category(branch_id: int, category_id: int, session: SessionDep, _: ManagerDep):
    await category_service.delete(session, category_id, branch_id)
