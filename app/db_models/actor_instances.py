from sqlalchemy import (
    Column, String, DateTime,
    ForeignKey, JSON, text,
    Enum
)
from sqlalchemy.sql import func
from app.db_models import Base, ModelDict
from app.db_models.workspaces import Workspace


class ActorInstance(Base, ModelDict):
    __tablename__ = 'actor_instances'

    id = Column(String(36), primary_key=True,
                   nullable=False, server_default=text("uuid_generate_v4()"))
    workspace_id = Column(String(36), ForeignKey(
        Workspace.id), nullable=False)
    actor_id = Column(String(36), ForeignKey('actors.id'), nullable=False)
    name = Column(String(255))
    configuration = Column(JSON)
    actor_type = Column(Enum('source', 'destination',
                             'generator', name='actor_instances_actor_type_enum'), nullable=False)
    user_id = Column(String(50))
    status = Column(Enum('active', 'inactive', name='actor_instances_status_enum'), server_default='active', nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ActorInstance(id='{self.id}', name='{self.name}', actor_type='{self.actor_type}', status='{self.status}')>"
