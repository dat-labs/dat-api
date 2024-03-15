from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class ActorInstance(Base):
    __tablename__ = 'actor_instances'

    id = Column(String(36), primary_key=True)
    workspace_id = Column(String(36), ForeignKey('workspaces.id'), nullable=False)
    actor_id = Column(String(36), ForeignKey('actors.id'), nullable=False)
    name = Column(String(255))
    configuration = Column(JSON)
    actor_type = Column(String(50))  # Assuming it's a string, change data type if necessary
    user_id = Column(String(50))
    status = Column(String(50))  # Assuming it's a string, change data type if necessary
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Define relationship with the Workspace model
    workspace = relationship('Workspace', back_populates="actor_instances")

    # Define relationship with the Actor model
    # actor = relationship("Actor", back_populates="actor_instances")

    def __repr__(self):
        return f"<ActorInstance(id='{self.id}', name='{self.name}', actor_type='{self.actor_type}', status='{self.status}')>"


class Workspace(Base):
    __tablename__ = 'workspaces'

    id = Column(String(36), primary_key=True)
    name = Column(String(50), nullable=False)
    status = Column(String(50))  # Assuming it's a string, change data type if necessary
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Define relationship with the ActorInstance model
    actor_instances = relationship(ActorInstance, back_populates="workspace")

    def __repr__(self):
        return f"<Workspace(id='{self.id}', name='{self.name}', status='{self.status}')>"


class Actor(Base):
    __tablename__ = 'actors'

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    icon = Column(String(255))
    actor_type = Column(Enum('source', 'destination',
                        'generator', name='actor_type_enum'))
    status = Column(Enum('active', 'inactive', name='actor_status_enum'))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<Actor(id='{self.id}', name='{self.name}', actor_type='{self.actor_type}', status='{self.status}')>"