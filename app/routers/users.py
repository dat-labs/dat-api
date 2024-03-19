import yaml
from datetime import datetime
import urllib.request
from fastapi import (APIRouter)
from ..services.users import user_service_dependency
from ..services.users.users import Users
from pydantic import BaseModel


class UserRequestModel(BaseModel):
    email: str
    password: str


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)



@router.post("/verify")
async def verify_user(user: UserRequestModel, service: Users = user_service_dependency):
    """
    Verify user credentials.

    Parameters:
    - user (UserRequestModel): User request model containing email and password.
    - service (Users): Instance of the Users service.

    Returns:
    - dict or None: Dictionary containing user information if credentials are valid.
    """
    return service.verify_user(user.email, user.password)


