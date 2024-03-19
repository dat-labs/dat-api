from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.sql import func
from app.db_models import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(String(36), primary_key=True,
                   nullable=False, server_default=text("uuid_generate_v4()"))
    email = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
