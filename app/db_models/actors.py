from sqlalchemy import Column, String, DateTime, Enum, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db_models import Base, ModelDict
from app.db_models.actor_instances import ActorInstance


class Actor(Base, ModelDict):
    __tablename__ = 'actors'

    id = Column(String(36), primary_key=True,
                nullable=False, server_default=text("uuid_generate_v4()"))
    name = Column(String(255), nullable=False)
    module_name = Column(String(255), nullable=False)
    icon = Column(String(255))
    actor_type = Column(Enum('source', 'destination',
                        'generator', name='actor_type_enum'), nullable=False)
    status = Column(Enum('active', 'inactive', name='actor_status_enum'), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    actor_instances = relationship(ActorInstance, backref="actor")

    def __repr__(self):
        return f"<Actor(id='{self.id}', name='{self.name}', actor_type='{self.actor_type}', status='{self.status}')>"
