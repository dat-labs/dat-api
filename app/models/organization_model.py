from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class OrganizationBase(BaseModel):
    name: str
    status: str

class OrganizationResponse(OrganizationBase):
    id: str
    created_at: datetime
    updated_at: datetime

class OrganizationPostRequest(OrganizationBase):
    pass

class OrganizationPutRequest(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
