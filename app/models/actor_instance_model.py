from typing import Dict, Any, Optional, List
from pydantic import BaseModel, root_validator
from ..models.actor_model import ActorResponse


ConnectorSpecificationConnectionSpec = Dict[str, Any]


class ActorInstanceBase(BaseModel):
    actor_id: str
    user_id: str
    name: str
    actor_type: str
    status: str = "active"
    configuration: ConnectorSpecificationConnectionSpec = {}


class ActorInstancePostRequest(ActorInstanceBase):
    pass


class ActorInstancePutRequest(BaseModel):
    actor_id: Optional[str] = None
    user_id: Optional[str] = None
    name: Optional[str] = None
    actor_type: Optional[str] = None
    status: Optional[str] = "active"
    configuration: Optional[ConnectorSpecificationConnectionSpec] = {}


class ActorInstanceResponse(ActorInstanceBase):
    id: str
    workspace_id: str
    actor: ActorResponse = None
    connected_connections: List[object] = []

class UploadResponse(BaseModel):
    bucket_name: str
    uploaded_path: str
    message: str