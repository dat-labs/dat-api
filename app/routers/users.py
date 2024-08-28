from fastapi import (APIRouter)
from ..services.users import user_service_dependency
from ..services.users.users import Users
from pydantic import BaseModel
from app.models.user_model import UserResponse


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

@router.get("/list")
async def fetch_users(service: Users = user_service_dependency):
    """
    Fetch all users.

    Parameters:
    - service (Users): Instance of the Users service.

    Returns:
    - list: List of all users.
    """
    return service.fetch_users()

@router.post("", response_model=UserResponse,
             description="Create a new user"
)
async def create_user(
    user: UserRequestModel,
    service: Users = user_service_dependency
) -> UserResponse:
    """
    Create a new user.

    Parameters:
    - user (UserRequestModel): User request model containing email and password.
    - service (Users): Instance of the Users service.

    Returns:
    - dict: Dictionary containing user information.
    """
    return service.create_user(user.email, user.password)

@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    description="Update a user"
)
async def update_user(
    user_id: str,
    user: UserRequestModel,
    service: Users = user_service_dependency
) -> UserResponse:
    """
    Update a user.

    Parameters:
    - user_id (str): ID of the user to update.
    - user (UserRequestModel): User request model containing email and password.
    - service (Users): Instance of the Users service.

    Returns:
    - dict: Dictionary containing updated user information.
    """
    return service.update_user(user_id, user.email, user.password)
