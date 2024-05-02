"""
Module for handling connection run logs using FastAPI.

This module contains endpoints and models for adding and retrieving connection run logs.

Classes:
    DatMessageRequest: Pydantic BaseModel for representing a request with DatMessage.

Functions:
    add_connection_run_log: Endpoint for adding a connection run log.
    get_connection_run_logs: Endpoint for getting all runs for a given connection ID.
    get_connection_runs_by_run_id: Endpoint for getting run logs for a particular run ID.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import StatementError
from pydantic import BaseModel
from dat_core.pydantic_models import DatMessage, Type
from app.db_models.connection_run_logs import ConnectionRunLogs
from app.models.connection_run_log_model import ConnectionRunLogResponse
from app.database import get_db

class DatMessageRequest(BaseModel):
    """Pydantic BaseModel for representing a request with DatMessage."""
    dat_message: DatMessage

router = APIRouter(
    prefix="/connection-run-logs",
    tags=["connection_run_logs"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.post("/", responses={403: {"description": "Operation forbidden"}},)
async def add_connection_run_log(
    connection_id: str,
    dat_message: DatMessage,
    run_id: str,
    db=Depends(get_db)
) -> ConnectionRunLogResponse:
    """
    Endpoint for adding a connection run log.

    Args:
        connection_id (str): The ID of the connection for which the log is being added.
        dat_message (DatMessage): The DatMessage object containing the log information.
        run_id (str): id of the run for which the log is being added
        db (Database Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        ConnectionRunLogResponse: The response containing the added connection run log.
    """
    try:
        if dat_message.type == Type.LOG:
            _msg = dat_message.log
        elif dat_message.type == Type.STATE:
            _msg = dat_message.state
        connection_run_log = ConnectionRunLogs(
            connection_id=connection_id,
            message=_msg.model_dump_json(),
            run_id=run_id,
            message_type=dat_message.type.value
        )
        db.add(connection_run_log)
        db.commit()
        db.refresh(connection_run_log)
        return connection_run_log
    except StatementError as exc:
        raise HTTPException(status_code=500, detail=repr(exc))
    except Exception as exc:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Something went wrong")


@router.get("/{connection_id}/runs",
             response_model=List[ConnectionRunLogResponse],
             description="Get all runs for a given connection id")
async def get_connection_run_logs(
    connection_id: str,
    db=Depends(get_db)
) -> List[ConnectionRunLogResponse]:
    """
    Endpoint for getting all runs for a given connection ID.

    Args:
        connection_id (str): The ID of the connection for which to retrieve the run logs.
        db (Database Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        List[ConnectionRunLogResponse]: A list of connection run logs for the given connection ID.
    """
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
async def get_connection_runs_by_run_id(
    run_id: str
) -> List[ConnectionRunLogResponse]:
    """
    Endpoint for getting run logs for a particular run ID.

    Args:
        run_id (str): The ID of the run for which to retrieve the run logs.

    Returns:
        List[ConnectionRunLogResponse]: A list of connection run logs for the given run ID.
    """
    db = list(get_db())[0]
    try:
        run_logs = db.query(ConnectionRunLogs).filter_by(run_id=run_id).all()
        return run_logs
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))
