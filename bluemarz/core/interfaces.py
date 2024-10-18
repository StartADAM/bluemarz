from abc import ABC, abstractmethod
from typing import Self

from bluemarz.core import models


class Session(ABC):
    def __init__(self, spec: models.SessionSpec):
        self._spec = spec

    @property
    def spec(self) -> models.SessionSpec:
        return self._spec

    @classmethod
    @abstractmethod
    def from_spec(cls, spec: models.SessionSpec) -> "Session":
        pass

    @abstractmethod
    def add_file(self, file: models.SessionFile) -> models.AddFileResult:
        pass

    @abstractmethod
    def add_message(self, message: models.SessionMessage) -> models.AddMessageResult:
        pass

    @abstractmethod
    def delete_session(self) -> models.DeleteSessionResult:
        pass

    @abstractmethod
    def add_tool_call_result(self, tool_call_result: models.ToolCallResult) -> models.AddMessageResult:
        pass

class Tool(ABC):
    def __init__(self, spec: models.ToolSpec):
        self._spec = spec

    @classmethod
    @abstractmethod
    def from_spec(cls, spec: models.ToolSpec) -> "Tool":
        pass

    @property
    def spec(self) -> models.ToolSpec:
        return self._spec


class SyncToolExecutor(ABC):
    @classmethod
    @abstractmethod
    def tool_name(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def execute_call(cls, toll_call: models.ToolCall):
        pass


class Agent(ABC):
    def __init__(self, spec: models.AgentSpec):
        self._spec = spec

    @classmethod
    @abstractmethod
    def from_spec(cls, spec: models.AgentSpec) -> "Agent":
        pass

    @abstractmethod
    def add_tools(self, tools: list[models.ToolSpec]) -> Self:
        pass

    @property
    def spec(self) -> models.AgentSpec:
        return self._spec


class AssignmentExecutor(ABC):
    @staticmethod
    @abstractmethod
    def validate_assignment(
        agent: Agent, session: Session, run_id: str | None, **kwargs
    ) -> None:
        pass
        
    @staticmethod
    @abstractmethod
    def execute(
        agent: Agent, session: Session, run_id: str | None, **kwargs
    ) -> models.RunResult:
        pass

    @staticmethod
    @abstractmethod
    def submit_tool_calls(
        agent: Agent,
        session: Session,
        run_id: str,
        tc_results: list[models.ToolCallResult],
        **kwargs,
    ) -> models.RunResult:
        pass

    @staticmethod
    @abstractmethod
    def prepare_for_async_tool_calls(
        agent: Agent,
        session: Session,
        run_id: str,
        **kwargs,
    ) -> models.RunResult:
        pass
