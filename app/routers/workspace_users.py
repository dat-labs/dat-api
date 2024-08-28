from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from sqlalchemy.orm import joinedload
from app.db_models.workspace_users import WorkspaceUser as WorkspaceUserModel
from app.database import get_db
from app.models.workspace_user_model import (
    WorkspaceUserResponse, WorkspaceUserPostRequest,
    WorkspaceUserPutRequest
)


router = APIRouter(
    prefix="/workspace_users",
    tags=["workspace_users"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/{workspace_id}/list",
    response_model=list[WorkspaceUserResponse],
    description="Fetch all available workspace users"
)
async def fetch_available_workspace_users(
    workspace_id: str,
    db=Depends(get_db)
) -> list[WorkspaceUserResponse]:
    """
    Fetches all available workspace users from the database.

    Args:
        workspace_id: The ID of the workspace.

    Returns:
        A list of available workspace users.
    """
    try:
        workspace_users = (
            db.query(WorkspaceUserModel)
            .filter_by(workspace_id=workspace_id)
            .all()
        )
        return workspace_users
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/",
    response_model=WorkspaceUserResponse,
    description="Create a new workspace user"
)
async def create_workspace_user(
    workspace_user: WorkspaceUserPostRequest,
    db=Depends(get_db)
) -> WorkspaceUserResponse:
    """
    Creates a new workspace user.

    Args:
        workspace_user: The workspace user to create.

    Returns:
        The created workspace user.
    """
    try:
        new_workspace_user = WorkspaceUserModel(
            **workspace_user.model_dump())
        db.add(new_workspace_user)
        db.commit()
        db.refresh(new_workspace_user)
        return new_workspace_user
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))