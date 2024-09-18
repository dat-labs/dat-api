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
import json
from datetime import datetime
from typing import List, Dict
import pydantic_core
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import StatementError
from pydantic import BaseModel
from dat_core.pydantic_models import DatMessage, Type, DatStateMessage, StreamState, DatLogMessage
from app.db_models.connection_run_logs import ConnectionRunLogs
from app.models.connection_run_log_model import ConnectionRunLogResponse
from app.models.agg_conn_run_log_model import (
    AggConnRunLogResponse, AggConnRunLogRuns, AggConnRunLogRunsStatus)
from app.database import get_db
from app.db_models.connections import Connection as ConnectionModel


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
        run_id (str): The ID of the run for which the log is being added.

    Returns:
        ConnectionRunLogResponse: The response containing the added connection run log.
    """
    try:
        # Ensure the connection belongs to the correct workspace
        connection = db.query(ConnectionModel).filter_by(id=connection_id).one_or_none()
        if connection is None:
            raise HTTPException(status_code=404, detail="Connection not found")

        _msg = dat_message.log if dat_message.type == Type.LOG else dat_message.state
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
        raise HTTPException(status_code=500, detail="Something went wrong")


@router.get("/{connection_id}/runs",
            response_model=List[ConnectionRunLogResponse],
            description="Get all runs for a given connection ID")
async def get_connection_run_logs(
    connection_id: str,
    workspace_id: str = Query(..., description="The workspace ID for scoping the connection"),
    db=Depends(get_db),
) -> List[ConnectionRunLogResponse]:
    """
    Endpoint for getting all runs for a given connection ID.

    Args:
        connection_id (str): The ID of the connection for which to retrieve the run logs.
        workspace_id (str): The ID of the workspace for scoping the connection.

    Returns:
        List[ConnectionRunLogResponse]: A list of connection run logs for the given connection ID.
    """
    try:
        # Ensure the connection belongs to the correct workspace
        connection = db.query(ConnectionModel).filter_by(id=connection_id, workspace_id=workspace_id).one_or_none()
        if connection is None:
            raise HTTPException(status_code=404, detail="Connection not found")

        run_logs = db.query(ConnectionRunLogs).filter_by(connection_id=connection_id).all()
        return run_logs
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/runs/{run_id}",
            response_model=List[ConnectionRunLogResponse],
            description="Get run logs for a particular run ID")
async def get_connection_runs_by_run_id(
    run_id: str,
    workspace_id: str = Query(..., description="The workspace ID for scoping the connection"),
    db=Depends(get_db),
) -> List[ConnectionRunLogResponse]:
    """
    Endpoint for getting run logs for a particular run ID.

    Args:
        run_id (str): The ID of the run for which to retrieve the run logs.
        workspace_id (str): The ID of the workspace for scoping the connection.

    Returns:
        List[ConnectionRunLogResponse]: A list of connection run logs for the given run ID.
    """
    try:
        # Fetch all logs with a valid run_id that belong to the correct workspace
        run_logs = (
            db.query(ConnectionRunLogs)
            .join(ConnectionModel, ConnectionRunLogs.connection_id == ConnectionModel.id)
            .filter(ConnectionRunLogs.run_id == run_id, ConnectionModel.workspace_id == workspace_id)
            .all()
        )
        run_logs.sort(key=get_emitted_at_from_conn_run_log)
        return run_logs
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{connection_id}/stream-states",
            response_model=Dict[str, StreamState],
            description="Get the latest stream states for a connection")
async def get_combined_stream_states(
    connection_id: str,
    workspace_id: str = Query(..., description="The workspace ID for scoping the connection"),
    db=Depends(get_db)
) -> Dict[str, StreamState]:
    combined_states = {}
    try:
        # Ensure the connection belongs to the correct workspace
        connection = db.query(ConnectionModel).filter_by(id=connection_id, workspace_id=workspace_id).one_or_none()
        if connection is None:
            raise HTTPException(status_code=404, detail="Connection not found")

        # Fetching state messages
        state_msgs = db.query(ConnectionRunLogs).filter_by(
            connection_id=connection_id, message_type='STATE'
        ).all()

        for _state_msg in state_msgs:
            _state_msg = DatStateMessage(**json.loads(_state_msg.message))
            if not _state_msg.stream_state.data:
                continue
            if _state_msg.stream.name not in combined_states:
                combined_states[_state_msg.stream.name] = {
                    'stream_state': _state_msg.stream_state, 
                    'emitted_at': _state_msg.emitted_at
                }
            elif combined_states[_state_msg.stream.name]['emitted_at'] < _state_msg.emitted_at:
                combined_states[_state_msg.stream.name] = {
                    'stream_state': _state_msg.stream_state, 
                    'emitted_at': _state_msg.emitted_at
                }
        return {_k: _v['stream_state'] for _k, _v in combined_states.items()}
    except StatementError as exc:
        raise HTTPException(status_code=500, detail=repr(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Something went wrong")


@router.get("/{connection_id}/agg-run-logs")
async def get_agg_run_logs(
    connection_id: str,
    workspace_id: str = Query(..., description="The workspace ID for scoping the connection"),
    db=Depends(get_db)
):
    try:
        # Ensure the connection belongs to the correct workspace
        connection = db.query(ConnectionModel).filter_by(id=connection_id, workspace_id=workspace_id).one_or_none()
        if connection is None:
            raise HTTPException(status_code=404, detail="Connection not found")

        # Fetching and sorting the connection run logs
        conn_run_logs = db.query(ConnectionRunLogs).filter_by(
            connection_id=connection_id
        ).order_by(ConnectionRunLogs.created_at.desc()).all()

        conn_run_logs.sort(key=get_emitted_at_from_conn_run_log, reverse=True)

        _runs_dct = {}
        runs = []

        for run_log in conn_run_logs:
            run_id = run_log.run_id
            if run_id not in _runs_dct:
                _runs_dct[run_id] = []
            _runs_dct[run_id].append(run_log)

        for run_id, run_logs in _runs_dct.items():
            start_time = datetime.fromtimestamp(
                get_emitted_at_from_conn_run_log(run_logs[-1])
            )
            end_time = None
            duration = None
            has_job_ended = is_job_ended(run_logs[0])
            if has_job_ended:
                end_time = datetime.fromtimestamp(
                    get_emitted_at_from_conn_run_log(run_logs[0])
                )
                duration = (end_time - start_time).seconds
            records_updated = get_int_from_list(run_logs)

            status = AggConnRunLogRunsStatus.RUNNING
            if has_job_ended:
                if has_errors():
                    if records_updated <= 0:
                        status = AggConnRunLogRunsStatus.FAILURE
                    else:
                        status = AggConnRunLogRunsStatus.PARTIAL_SUCCESS
                else:
                    if records_updated <= 0:
                        status = AggConnRunLogRunsStatus.PARTIAL_SUCCESS
                    else:
                        status = AggConnRunLogRunsStatus.SUCCESS

            run_res = AggConnRunLogRuns(
                id=run_id,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                status=status,
                records_updated=records_updated,
            )
            runs.append(run_res)

        response = AggConnRunLogResponse(
            connection_id=connection_id,
            total_runs=len(_runs_dct.keys()),
            runs=runs,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_int_from_list(run_logs: List) -> int:
    ''''''
    rec_upd8d = 0
    for run_log in run_logs:
        try:
            rec_upd8d += json.loads(json.loads(run_log.message).get('message', '{}')).get('n_docs_processed', 0)
        except (json.decoder.JSONDecodeError, AttributeError):
            pass
    return rec_upd8d


def get_emitted_at_from_conn_run_log(conn_run_log: ConnectionRunLogs) -> int:
    '''Will return UNIX timestamp'''
    # print(f'conn_run_log.message: {conn_run_log.message}')
    try:
        return DatLogMessage(**json.loads(conn_run_log.message)).emitted_at
    except json.decoder.JSONDecodeError:
        print(f'Unable to parse {conn_run_log.message} as JSON.')
        return 0
    except pydantic_core._pydantic_core.ValidationError:
        try:
            return json.loads(conn_run_log.message)['emitted_at']
        except KeyError:
            print(f'KeyError: {conn_run_log.message}')
            return 0
    except Exception as _e:
        print(f'{_e}: {conn_run_log}')
        return 0


def is_job_ended(conn_run_log: ConnectionRunLogs) -> bool:
    try:
        if json.loads(conn_run_log.message)['message'] == 'Job run ended':
            return True
    except Exception as _e:
        print(_e)
    return False


def has_errors():
    return False
    return True
