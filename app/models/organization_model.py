from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class OrganizationBase(BaseModel):
    name: str
    status: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class OrganizationResponse(OrganizationBase):
    id: str

class OrganizationPostRequest(OrganizationBase):
    pass

class OrganizationPutRequest(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
