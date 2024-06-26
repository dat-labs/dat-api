from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from app.db_models import Base
from app.db_models.organizations import Organization


class Workspace(Base):
    __tablename__ = 'workspaces'

    id = Column(String(36), primary_key=True,
                nullable=False, server_default="uuid_generate_v4()")
    organization_id = Column(String(36),  ForeignKey(Organization.id), nullable=False)
    name = Column(String(50), nullable=False)
    status = Column(Enum('active', 'inactive', name='workspaces_status_enum'), server_default='active', nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Workspace(id='{self.id}', name='{self.name}', status='{self.status}')>"
