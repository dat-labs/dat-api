import datetime
from typing import List
from pydantic import BaseModel


class AggConnRunLogRunRecordsPerStream(BaseModel):
    stream: str
    docs_fetched: int
    records_updated: int


class AggConnRunLogRuns(BaseModel):
    id: str
    # status: str  # TODO: Need to decide  where this value will get populated from
    start_time: datetime.datetime
    end_time: datetime.datetime
    duration: int
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
