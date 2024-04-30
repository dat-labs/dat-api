import enum
from datetime import datetime
from sqlalchemy import Column, String, Text, Enum, DateTime, ForeignKey, text
from app.db_models import Base


class LogLevel(enum.Enum):
    FATAL = 'FATAL'
    ERROR = 'ERROR'
    WARN = 'WARN'
    INFO = 'INFO'
    DEBUG = 'DEBUG'
    TRACE = 'TRACE'


class ConnectionRunLogs(Base):
    __tablename__ = 'connection_run_logs'

    id = Column(String(36),
                primary_key=True,
                nullable=False,
                server_default=text("uuid_generate_v4()"))
    connection_id = Column(String(36), ForeignKey(
        'connections.id'), nullable=False)
    level = Column(Enum(LogLevel), nullable=False)
    message = Column(String, nullable=False)
    stack_trace = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    run_id = Column(String(36),
                nullable=False, server_default=text("uuid_generate_v4()"))

    def __repr__(self):
        return f"<ConnectionRunLogs(id={self.id}, connection_id={self.connection_id}, run_id={self.run_id}, level={self.level}, message='{self.message[:20]}...', created_at={self.created_at}, updated_at={self.updated_at})>"
