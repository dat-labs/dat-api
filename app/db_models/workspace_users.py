from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db_models import Base


class WorkspaceUser(Base):
    __tablename__ = 'workspace_users'

    id = Column(String(36), primary_key=True,
                nullable=False, server_default="uuid_generate_v4()")
    workspace_id = Column(String(36), ForeignKey(
        'workspaces.id'), nullable=False)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<WorkspaceUser(id='{self.id}', workspace_id='{self.workspace_id}', user_id='{self.user_id}')>"
