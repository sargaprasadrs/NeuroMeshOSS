from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from typing import Any, Dict
from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Run(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    status: RunStatus = RunStatus.PENDING
    current_state: Dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        frozen = True


class RunStep(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    node_id: str
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Dict[str, Any] = Field(default_factory=dict)
    traces: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        frozen = True
