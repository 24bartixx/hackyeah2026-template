from fastapi import APIRouter

from app.dependencies import CurrentUserDep
from app.models import User
from app.schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: CurrentUserDep) -> User:
    return current_user
