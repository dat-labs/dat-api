from pydantic import BaseModel
from typing import Optional, Dict
from .user_model import UserResponse
from .workspace_model import WorkspaceResponse


class WorkspaceUserExtraAttributes(BaseModel):
    user: UserResponse

class WorkspaceUserBase(BaseModel):
    workspace_id: str
    user_id: str

class WorkspaceUserResponse(WorkspaceUserBase, WorkspaceUserExtraAttributes):
    id: str

class WorkspaceUserPostRequest(WorkspaceUserBase):
    pass

class WorkspaceUserPutRequest(BaseModel):
    workspace_id: Optional[str] = None
    user_id: Optional[str] = None
