from typing import List
from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from pydantic import BaseModel
from dat_core.pydantic_models.dat_log_message import DatLogMessage
from app.db_models.connection_run_logs import ConnectionRunLogs
from app.models.connection_run_log_model import ConnectionRunLogResponse
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
        db_dat_log_message = ConnectionRunLogs(**dat_log_message_dct)
        db.add(db_dat_log_message)
        db.commit()
        db.refresh(db_dat_log_message)
        db_dat_log_message.level = dat_log_message.model_dump().get('level').name
        return db_dat_log_message
    except Exception as e:
        raise HTTPException(status_code=403, detail="Operation forbidden")


@router.post("/{connection_id}/runs",
             response_model=List[ConnectionRunLogResponse],
             description="Get all runs for a given connection id")
async def get_connection_run_logs(
    connection_id: str,
    db=Depends(get_db)
) -> List[ConnectionRunLogResponse]:
    db = list(get_db())[0]
    try:
        run_logs = db.query(ConnectionRunLogs).filter_by(
            connection_id=connection_id).all()
        return run_logs
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/runs/{run_id}",
            response_model=List[ConnectionRunLogResponse],
            description="Get run logs for a particular run id")
async def get_connection_run_by_run_id(
    run_id: str
) -> List[ConnectionRunLogResponse]:
    db = list(get_db())[0]
    try:
        run_logs = db.query(ConnectionRunLogs).filter_by(run_id=run_id).all()
        return run_logs
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))
