from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Enum, text
from sqlalchemy.sql import func
from app.db_models import Base, ModelDict


class Connection(Base, ModelDict):
    __tablename__ = 'connections'

    id = Column(String(36), primary_key=True,
                   nullable=False, server_default=text("uuid_generate_v4()"))
    workspace_id = Column(String(36), ForeignKey('workspaces.id'), nullable=False)
    source_instance_id = Column(String(36), ForeignKey('actor_instances.id'), nullable=False)
    generator_instance_id = Column(String(36), ForeignKey('actor_instances.id'), nullable=False)
    destination_instance_id = Column(String(36), ForeignKey('actor_instances.id'), nullable=False)
    name = Column(String(255))
    namespace_format = Column(String(255), default="${SOURCE_NAMESPACE}")
    prefix = Column(String(255))
    configuration = Column(JSON)
    catalog = Column(JSON)
    schedule = Column(JSON)
    schedule_type = Column(Enum('manual', 'scheduled', name='schedule_type_enum'), nullable=False, server_default='manual')
    status = Column(Enum('active', 'inactive', name='connection_status_enum'), server_default='active', nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Connection(id='{self.id}', name='{self.name}', status='{self.status}')>"
