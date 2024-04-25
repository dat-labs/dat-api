from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from app.db_models import Base


class Organization(Base):
    __tablename__ = 'organizations'

    id = Column(String(36), primary_key=True,
                nullable=False, server_default="uuid_generate_v4()")
    name = Column(String(50), nullable=False)
    status = Column(Enum('active', 'inactive', name='organizations_status_enum'),
                    server_default='active', nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Organization(id='{self.id}', name='{self.name}', status='{self.status}')>"
