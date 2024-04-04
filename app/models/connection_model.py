from typing import Dict, Optional
from pydantic import BaseModel
from dat_core.pydantic_models import (
    DatCatalog,
    Connection as ConnectionPdModel
)

class Cron(BaseModel):
    cron_expression: str
    timezone: Optional[str] = None

class Schedule(BaseModel):
    cron: Optional[Cron] = None


class ConnectionBase(BaseModel):
    source_instance_id: str
    generator_instance_id: str
    destination_instance_id: str
    workspace_id: str
    name: str
    namespace_format: str = "${SOURCE_NAMESPACE}"
    prefix: Optional[str] = None
    configuration: Optional[Dict] = None
    catalog: Optional[DatCatalog] = None
    schedule: Optional[Schedule] = None
    schedule_type: Optional[str] = "manual"
    status: Optional[str] = "active"


class ConnectionResponse(ConnectionBase):
    id: str

class ConnectionPostRequest(ConnectionBase):
    pass

class ConnectionPutRequest(BaseModel):
    name: Optional[str] = None
    namespace_format: Optional[str] = None
    prefix: Optional[str] = None
    configuration: Optional[Dict] = None
    catalog: Optional[DatCatalog] = None
    schedule: Optional[Schedule] = None
    schedule_type: Optional[str] = "manual"
    status: Optional[str] = "active"


class ConnectionOrchestraResponse(ConnectionBase, ConnectionPdModel):
    pass
