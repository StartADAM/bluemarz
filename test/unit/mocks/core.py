from typing import Self

from bluemarz.core.interfaces import Agent, AssignmentExecutor, Session
from bluemarz.core.models import (
    AddFileResult,
    AddMessageResult,
    AgentSpec,
    DeleteSessionResult,
    RunResult,
    SessionSpec,
    ToolCallResult,
    ToolSpec,
)
from bluemarz.core.registries import assignment_executor


class MockSession(Session):
    def __init__(self, spec: SessionSpec):
        super().__init__(spec)

    def add_file(self) -> AddFileResult:
        return super().add_file()

    def add_message(self) -> AddMessageResult:
        return super().add_message()

    def delete_session(self) -> DeleteSessionResult:
        return super().delete_session()


class MockAgent(Agent):
    def __init__(self, spec: AgentSpec):
        super().__init__(spec)

    def add_tools(self, tools: list[ToolSpec]) -> Self:
        return super().add_tools(tools)


@assignment_executor
class MockExecutor(AssignmentExecutor):
    @staticmethod
    def execute(
        agent: Agent, session: Session, run_id: str | None, **kwargs
    ) -> RunResult:
        return super().execute(agent, session, run_id, **kwargs)

    @staticmethod
    def submit_tool_calls(
        agent: Agent,
        session: Session,
        run_id: str,
        tc_results: list[ToolCallResult],
        **kwargs,
    ) -> RunResult:
        return super().submit_tool_calls(agent, session, run_id, tc_results, **kwargs)
