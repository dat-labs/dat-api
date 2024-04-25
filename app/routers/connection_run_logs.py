from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from pydantic import BaseModel
from dat_core.pydantic_models.dat_log_message import DatLogMessage
from app.db_models.connection_run_logs import ConnectionRunLogs as ConnectionRunLogsModel
from app.database import get_db


class DatLogMessageRequest(BaseModel):
    dat_log_message: DatLogMessage


router = APIRouter(
    prefix="/connection-run-logs",
    tags=["connection_run_logs"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.post("/", responses={403: {"description": "Operation forbidden"}},)
async def add_connection_run_log(
    connection_id: str,
    dat_log_message: DatLogMessage,
    db=Depends(get_db)
) -> DatLogMessage:
    try:
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
