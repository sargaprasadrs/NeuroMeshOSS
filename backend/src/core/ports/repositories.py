from abc import ABC, abstractmethod
from uuid import UUID
from typing import List, Sequence
from src.core.entities.user import User
from src.core.entities.workflow import Workflow
from src.core.entities.run import Run, RunStep


class IUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        pass


class IWorkflowRepository(ABC):
    @abstractmethod
    async def get_by_id(self, workflow_id: UUID) -> Workflow | None:
        pass

    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> Sequence[Workflow]:
        pass

    @abstractmethod
    async def save(self, workflow: Workflow) -> Workflow:
        pass


class IRunRepository(ABC):
    @abstractmethod
    async def get_by_id(self, run_id: UUID) -> Run | None:
        pass

    @abstractmethod
    async def save(self, run: Run) -> Run:
        pass

    @abstractmethod
    async def save_step(self, step: RunStep) -> RunStep:
        pass

    @abstractmethod
    async def get_steps(self, run_id: UUID) -> Sequence[RunStep]:
        pass
