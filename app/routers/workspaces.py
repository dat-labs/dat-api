from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from app.db_models.workspaces import Workspace as WorkspaceModel
from app.database import get_db
from app.models.workspace_model import (
    WorkspaceResponse, WorkspacePostRequest,
    WorkspacePutRequest
)


router = APIRouter(
    prefix="/workspaces",
    tags=["workspaces"],
    responses={404: {"description": "Not found"}},
)

@router.get(
    "/default",
    response_model=WorkspaceResponse
)
async def get_default_workspace(
    db=Depends(get_db)
) -> WorkspaceResponse:
    """
    Fetches the default workspace.
    """
    workspace = db.query(WorkspaceModel).filter_by(
        name="Default", status="active").first()
    if workspace is None:
        raise HTTPException(status_code=404, detail="Default workspace not found")
    return workspace

@router.get(
    "/list",
    response_model=list[WorkspaceResponse],
    description="Fetch all available workspaces" 
)
async def fetch_available_workspaces(
    db=Depends(get_db)
) -> list[WorkspaceResponse]:
    """
    Fetches all available workspaces from the database.

    Returns:
        A list of available workspaces.
    """
    try:
        workspaces = db.query(WorkspaceModel).all()
        return workspaces
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse
)
async def read_workspace(
    workspace_id: str,
    db=Depends(get_db)
) -> WorkspaceResponse:
    """
    Retrieves a workspace by its ID.

    Args:
        workspace_id: The ID of the workspace.

    Returns:
        The workspace with the specified ID.

    Raises:
        HTTPException: If the workspace is not found.
    """
    workspace = db.query(WorkspaceModel).get(workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace

@router.post(
    "",
    response_model=WorkspaceResponse
)
async def create_workspace(
    payload: WorkspacePostRequest,
    db=Depends(get_db)
) -> WorkspaceResponse:
    """
    Creates a new workspace.
    """
    try:
        workspace = WorkspaceModel(
            **payload.model_dump(exclude_unset=True)
        )
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
        return workspace
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.put(
    "/{workspace_id}",
    response_model=WorkspaceResponse
)
async def update_workspace(
    workspace_id: str,
    payload: WorkspacePutRequest,
    db=Depends(get_db)
) -> WorkspaceResponse:
    """
    Update a workspace.
    """
    workspace = db.query(WorkspaceModel).get(workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(workspace, key, value)
        db.commit()
        db.refresh(workspace)
        return workspace
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.delete(
    "/{workspace_id}",
)
async def delete_workspace(
    workspace_id: str,
    db=Depends(get_db)
) -> None:
    """
    Delete a workspace.
    """
    workspace = db.query(WorkspaceModel).get(workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        db.delete(workspace)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))
