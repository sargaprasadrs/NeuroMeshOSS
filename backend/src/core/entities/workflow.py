from uuid import UUID, uuid4
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class WorkflowNode(BaseModel):
    id: str
    type: str
    data: Dict[str, Any] = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    source: str
    target: str
    condition: str | None = None


class WorkflowDefinition(BaseModel):
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]


class Workflow(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    name: str
    definition: WorkflowDefinition
    is_active: bool = True
    version: int = 1

    class Config:
        frozen = True
