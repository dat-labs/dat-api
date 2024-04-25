from pydantic import BaseModel
from typing import Optional


class WorkspaceBase(BaseModel):
    organization_id: str
    name: str
    status: str

class WorkspaceResponse(WorkspaceBase):
    id: str

class WorkspacePostRequest(WorkspaceBase):
    pass

class WorkspacePutRequest(BaseModel):
    organization_id: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None
