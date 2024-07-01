import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class AggConnRunLogRunRecordsPerStream(BaseModel):
    stream: str
    docs_fetched: int
    records_updated: int


class AggConnRunLogRunsStatus(Enum):
    QUEUED = 'QUEUED'
    RUNNING = 'RUNNING'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    PARTIAL_SUCCESS = 'PARTIAL_SUCCESS'


class AggConnRunLogRuns(BaseModel):
    id: str
    status: AggConnRunLogRunsStatus
    start_time: datetime.datetime
    end_time: Optional[datetime.datetime]
    duration: Optional[int]
    # duration_human_readable: str
    # docs_size: int
    # docs_size_human_readable: str
    # docs_fetched: int
    records_updated: int
    # records_per_stream: List[AggConnRunLogRunRecordsPerStream]


class AggConnRunLogResponse(BaseModel):

    connection_id: str
    total_runs: int
    # current_page: int
    # page_size: int
    # from_datetime: datetime.datetime
    # to_datetime: datetime.datetime
    runs: List[AggConnRunLogRuns]
