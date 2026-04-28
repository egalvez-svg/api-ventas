from fastapi import APIRouter
from sqlmodel import select

from app.core.deps import SessionDep
from app.models.base import Branch
from app.schemas.branch import BranchRead

router = APIRouter(prefix="/branches", tags=["Branches"])


@router.get("/", response_model=list[BranchRead])
async def list_branches(session: SessionDep):
    """
    List all branches. Accessible by any authenticated user (or even public if needed, 
    but currently protected by default if using global dependencies, though here 
    we don't have a global auth dependency on the router yet).
    """
    result = await session.exec(select(Branch).where(Branch.is_active == True))
    return result.all()
