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
import re
import json
from typing import List, Dict
import pydantic_core
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import StatementError
from pydantic import BaseModel
from dat_core.pydantic_models import DatMessage, Type, DatStateMessage, StreamState, DatLogMessage
from app.db_models.connection_run_logs import ConnectionRunLogs
from app.models.connection_run_log_model import ConnectionRunLogResponse
from app.models.agg_conn_run_log_model import AggConnRunLogResponse, AggConnRunLogRuns
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
    try:
        run_logs = db.query(ConnectionRunLogs).filter_by(run_id=run_id).all()
        return run_logs
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{connection_id}/stream-states",
            response_model=Dict[str, StreamState],
            description="Get the latest stream states for a connection")
async def get_combined_stream_states(
    connection_id: str,
    db=Depends(get_db)
) -> Dict[str, StreamState]:
    combined_states = {}
    try:
        state_msgs = db.query(ConnectionRunLogs).filter_by(
            connection_id=connection_id, message_type='STATE')
        for _state_msg in state_msgs:
            _state_msg = DatStateMessage(**json.loads(_state_msg.message))
            if _state_msg.stream.namespace not in combined_states:
                combined_states[_state_msg.stream.namespace] = _state_msg.stream_state
            elif combined_states[_state_msg.stream.namespace].emitted_at < _state_msg.stream_state.emitted_at:
                combined_states[_state_msg.stream.namespace] = _state_msg.stream_state
        return combined_states
    except StatementError as exc:
        raise HTTPException(status_code=500, detail=repr(exc))
    except Exception as exc:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Something went wrong")


@router.get("/{connection_id}/agg-run-logs")
async def get_agg_run_logs(
    connection_id: str,
    db=Depends(get_db)
):
    # casting to list to load to memory
    conn_run_logs = db.query(ConnectionRunLogs).filter_by(
        connection_id=connection_id).order_by(
            ConnectionRunLogs.created_at.desc()).all()
    
    _runs_dct = {}
    runs = []

    for run_log in conn_run_logs:
        run_id = run_log.run_id
        if run_id not in _runs_dct:
            _runs_dct[run_id] = []
        _runs_dct[run_id].append(run_log)
    
    for run_id, run_logs in _runs_dct.items():
        start_time = run_logs[-1].created_at
        end_time = run_logs[0].updated_at
        records_updated = 0
        for run_log_msg in run_logs:
            # print(run_id, records_updated)
            try:
                message = DatLogMessage(
                    **json.loads(run_log_msg.message)).message
            except pydantic_core._pydantic_core.ValidationError:
                message = ''
            match = re.search(r'\b\d+\b', message)
            if match:
                # print(run_log_msg)
                records_updated += int(match.group(0))
        run_res = AggConnRunLogRuns(
            id=run_id,
            start_time=start_time,
            end_time=end_time,
            duration=(end_time-start_time).seconds,
            records_updated=records_updated,
        )
        runs.append(run_res)
    
    response = AggConnRunLogResponse(
        connection_id=connection_id,
        total_runs=len(_runs_dct.keys()),
        runs=runs,
    )
    print('========', response)
    return {
        "total_runs": 10,
        "page_number": 1,
        "page_size": 10,
        "from_datetime": "2021-09-01T00:00:00Z",
        "to_datetime": "2021-09-01T23:59:59Z",
        "runs": [
            {
                "id": "1",
                "status": "success",
                "start_time": "2021-09-01T10:00:00Z",
                "end_time": "2021-09-01T10:30:00Z",
                "duration": "30 mins",
                "size": "10 MB",
                "documents_fetched": 1000,
                "destination_record_updated": 1000,
                "records_per_stream": [
                    {
                        "stream": "pdf",
                        "documents_fetched": 500,
                        "destination_record_updated": 500
                    },
                    {
                        "stream": "csv",
                        "documents_fetched": 500,
                        "destination_record_updated": 500
                    }
                ]
            },
        ]
    }
