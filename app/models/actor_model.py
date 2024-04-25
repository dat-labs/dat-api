from pydantic import BaseModel
from typing import Optional


class ActorBase(BaseModel):
    name: str
    module_name: str
    icon: Optional[str] = None
    actor_type: str
    status: str = "active"

class ActorPostRequest(ActorBase):
    pass

class ActorPutRequest(BaseModel):
    name: Optional[str] = None
    module_name: Optional[str] = None
    icon: Optional[str] = None
    actor_type: Optional[str] = None
    status: str = "active"

class ActorResponse(ActorBase):
    id: str