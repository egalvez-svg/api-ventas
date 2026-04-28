from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.core.deps import CurrentUser, SessionDep, require_roles
from app.models.base import Branch
from app.schemas.branch import BranchCreate, BranchRead, BranchUpdate

router = APIRouter(prefix="/branches", tags=["Branches"])

AdminOnly = Depends(require_roles("admin"))


@router.get("/", response_model=list[BranchRead])
async def list_branches(session: SessionDep, _: CurrentUser):
    result = await session.exec(select(Branch).where(Branch.is_active == True))
    return result.all()


@router.get("/{branch_id}", response_model=BranchRead)
async def get_branch(branch_id: int, session: SessionDep, _: CurrentUser):
    branch = await session.get(Branch, branch_id)
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    return branch


@router.post("/", response_model=BranchRead, status_code=status.HTTP_201_CREATED, dependencies=[AdminOnly])
async def create_branch(branch_in: BranchCreate, session: SessionDep):
    existing = await session.exec(select(Branch).where(Branch.name == branch_in.name))
    if existing.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Branch name already exists")

    branch = Branch(**branch_in.model_dump())
    session.add(branch)
    await session.commit()
    await session.refresh(branch)
    return branch


@router.patch("/{branch_id}", response_model=BranchRead, dependencies=[AdminOnly])
async def update_branch(branch_id: int, branch_in: BranchUpdate, session: SessionDep):
    branch = await session.get(Branch, branch_id)
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

    data = branch_in.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(branch, field, value)

    session.add(branch)
    await session.commit()
    await session.refresh(branch)
    return branch


@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[AdminOnly])
async def deactivate_branch(branch_id: int, session: SessionDep):
    branch = await session.get(Branch, branch_id)
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

    branch.is_active = False
    session.add(branch)
    await session.commit()
