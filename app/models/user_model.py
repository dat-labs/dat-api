from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    email: str
    password_hash: str
    created_at: datetime
    updated_at: datetime

class UserResponse(UserBase):
    id: str
