from typing import Dict, Any, Optional
from pydantic import BaseModel
from ..models.actor_model import ActorResponse


ConnectorSpecificationConnectionSpec = Dict[str, Any]


class ActorInstanceBase(BaseModel):
    workspace_id: str
    actor_id: str
    user_id: str
    name: str
    actor_type: str
    status: str
    configuration: ConnectorSpecificationConnectionSpec = {}


class ActorInstancePostRequest(ActorInstanceBase):
    pass


class ActorInstancePutRequest(BaseModel):
    workspace_id: Optional[str] = None
    actor_id: Optional[str] = None
    user_id: Optional[str] = None
    name: Optional[str] = None
    actor_type: Optional[str] = None
    status: Optional[str] = None
    configuration: Optional[ConnectorSpecificationConnectionSpec] = {}


class ActorInstanceResponse(ActorInstanceBase):
    id: str


class ActorInstanceGetResponse(ActorInstanceResponse):
    actor: Optional[ActorResponse] = None
