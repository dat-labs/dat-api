# import json
from uuid import uuid4
from fastapi import (APIRouter,
                     HTTPException)
from pydantic import BaseModel
# from dat_core.pydantic_models.connector_specification import ConnectorSpecification
# from dat_core.pydantic_models.dat_catalog import DatCatalog
from dat_core.pydantic_models.dat_log_message import DatLogMessage
# from dat_core.pydantic_models.configured_document_stream import ConfiguredDocumentStream
from ..db_models.workspaces import Workspace
from ..db_models.connections import Connection
from ..db_models.connection_run_logs import ConnectionRunLogs as ConnectionRunLogsModel, LogLevel


from ..database import get_db

class DatLogMessageRequest(BaseModel):
    # uuid: str = str(uuid4())
    dat_log_message: DatLogMessage



router = APIRouter(
    prefix="/connection_run_logs",
    tags=["connection_run_logs"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)




@router.post("/", responses={403: {"description": "Operation forbidden"}},)
async def add_connection_run_log(
    connection_id: str,
    dat_log_message: DatLogMessage) -> DatLogMessage:
    try:
        db = list(get_db())[0]
        dat_log_message_dct = dat_log_message.model_dump()
        dat_log_message_dct.update({
            'level': dat_log_message_dct['level'].name,
            'connection_id': connection_id,
        })
        db_dat_log_message = ConnectionRunLogsModel(**dat_log_message_dct)
        db.add(db_dat_log_message)
        db.commit()
        db.refresh(db_dat_log_message)
        db_dat_log_message.level = dat_log_message.model_dump().get('level').name
        return db_dat_log_message
    except Exception as e:
        raise
        raise HTTPException(status_code=403, detail="Operation forbidden")
