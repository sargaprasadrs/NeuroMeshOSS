from uuid import UUID
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.entities.user import User
from src.core.entities.workflow import Workflow, WorkflowDefinition
from src.core.entities.run import Run, RunStep, RunStatus
from src.core.ports.repositories import IUserRepository, IWorkflowRepository, IRunRepository
from src.adapters.database.models import UserModel, WorkflowModel, RunModel, RunStepModel


class SqlAlchemyUserRepository(IUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            is_active=model.is_active,
            role=model.role,
        )

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.get(UserModel, user_id)
        return self._to_entity(result) if result else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, user: User) -> User:
        model = await self.session.get(UserModel, user.id)
        if not model:
            model = UserModel(
                id=user.id,
                email=user.email,
                password_hash=user.password_hash,
                is_active=user.is_active,
                role=user.role,
            )
            self.session.add(model)
        else:
            model.email = user.email
            model.password_hash = user.password_hash
            model.is_active = user.is_active
            model.role = user.role
        await self.session.flush()
        return self._to_entity(model)


class SqlAlchemyWorkflowRepository(IWorkflowRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _to_entity(self, model: WorkflowModel) -> Workflow:
        return Workflow(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            definition=WorkflowDefinition.model_validate(model.definition),
            is_active=model.is_active,
            version=model.version,
        )

    async def get_by_id(self, workflow_id: UUID) -> Workflow | None:
        model = await self.session.get(WorkflowModel, workflow_id)
        return self._to_entity(model) if model else None

    async def list_by_user(self, user_id: UUID) -> Sequence[Workflow]:
        stmt = select(WorkflowModel).where(WorkflowModel.user_id == user_id)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def save(self, workflow: Workflow) -> Workflow:
        model = await self.session.get(WorkflowModel, workflow.id)
        if not model:
            model = WorkflowModel(
                id=workflow.id,
                user_id=workflow.user_id,
                name=workflow.name,
                definition=workflow.definition.model_dump(),
                is_active=workflow.is_active,
                version=workflow.version,
            )
            self.session.add(model)
        else:
            model.name = workflow.name
            model.definition = workflow.definition.model_dump()
            model.is_active = workflow.is_active
            model.version = workflow.version
        await self.session.flush()
        return self._to_entity(model)


class SqlAlchemyRunRepository(IRunRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _to_entity(self, model: RunModel) -> Run:
        return Run(
            id=model.id,
            workflow_id=model.workflow_id,
            status=RunStatus(model.status),
            current_state=model.current_state,
            version=model.version,
            created_at=model.created_at,
        )

    def _step_to_entity(self, model: RunStepModel) -> RunStep:
        return RunStep(
            id=model.id,
            run_id=model.run_id,
            node_id=model.node_id,
            input=model.input,
            output=model.output,
            traces=model.traces,
            duration_ms=model.duration_ms,
            created_at=model.created_at,
        )

    async def get_by_id(self, run_id: UUID) -> Run | None:
        model = await self.session.get(RunModel, run_id)
        return self._to_entity(model) if model else None

    async def save(self, run: Run) -> Run:
        model = await self.session.get(RunModel, run.id)
        if not model:
            model = RunModel(
                id=run.id,
                workflow_id=run.workflow_id,
                status=run.status.value,
                current_state=run.current_state,
                version=run.version,
                created_at=run.created_at,
            )
            self.session.add(model)
        else:
            # Optimistic Concurrency Control (OCC) Check
            if model.version != run.version:
                raise ValueError("Concurrency collision: Run state has been updated by another worker thread.")
            model.status = run.status.value
            model.current_state = run.current_state
            model.version = run.version + 1
        await self.session.flush()
        return self._to_entity(model)

    async def save_step(self, step: RunStep) -> RunStep:
        model = await self.session.get(RunStepModel, step.id)
        if not model:
            model = RunStepModel(
                id=step.id,
                run_id=step.run_id,
                node_id=step.node_id,
                input=step.input,
                output=step.output,
                traces=step.traces,
                duration_ms=step.duration_ms,
                created_at=step.created_at,
            )
            self.session.add(model)
        else:
            model.node_id = step.node_id
            model.input = step.input
            model.output = step.output
            model.traces = step.traces
            model.duration_ms = step.duration_ms
        await self.session.flush()
        return self._step_to_entity(model)

    async def get_steps(self, run_id: UUID) -> Sequence[RunStep]:
        stmt = select(RunStepModel).where(RunStepModel.run_id == run_id).order_index(RunStepModel.created_at)
        # Using basic order_by (order_index was a typo in drafting)
        stmt = select(RunStepModel).where(RunStepModel.run_id == run_id).order_by(RunStepModel.created_at)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._step_to_entity(m) for m in models]
