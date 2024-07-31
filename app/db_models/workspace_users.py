from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from app.db_models import Base
from app.db_models.workspaces import Workspace
from app.db_models.users import User


class WorkspaceUser(Base):
    __tablename__ = 'workspace_users'

    id = Column(String(36), primary_key=True,
                nullable=False, server_default="uuid_generate_v4()")
    workspace_id = Column(String(36), ForeignKey(
        Workspace.id), nullable=False)
    user_id = Column(String(36), ForeignKey(User.id), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
