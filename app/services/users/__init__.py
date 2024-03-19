from sqlalchemy.orm import Session
from ...database import get_db
from fastapi import Depends
from .users import Users

def get_service(db_session: Session = Depends(get_db)):
    return Users(db_session)

user_service_dependency = Depends(get_service)