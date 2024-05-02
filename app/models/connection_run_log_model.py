import datetime
from pydantic import BaseModel

class ConnectionRunLogResponse(BaseModel):

    connection_id: str
    message: str
    stack_trace: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    run_id: str
    message_type: str