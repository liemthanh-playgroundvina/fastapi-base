from typing import Optional, Any
from pydantic import BaseModel, validator, root_validator
from datetime import datetime


class QueueTimeHandle(BaseModel):
    start_generate: str = None
    end_generate: str = None


class QueueStatusHandle(BaseModel):
    general_status: str = "PENDING"
    task_status: str = None


class QueueResult(BaseModel):
    task_id: str
    status: dict = None
    time: dict = None
    queue: Any = None
    task_result: Any = None
    error: Optional[Any] = None


class QueueResponse(BaseModel):
    status: str = "PENDING"
    time: datetime
    task_id: str
