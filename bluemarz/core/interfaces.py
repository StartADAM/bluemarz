from abc import ABC, abstractmethod
from typing import Self, TypeVar

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


class ToolDefinition(ABC):
    def __init__(self, spec: models.ToolSpec, executor: "ToolImplementation" = None):
        self._spec = spec
        self._executor = executor

    @classmethod
    def from_spec(cls, spec: models.ToolSpec) -> "ToolDefinition":
        return cls(spec, None)

    @classmethod
    def from_implementation(cls, executor: "ToolImplementation") -> "ToolDefinition":
        return cls.from_spec(executor.spec, executor)

    @property
    def spec(self) -> models.ToolSpec:
        return self._spec

    @property
    def executor(self) -> "ToolImplementation":
        return self._executor
    

class ToolImplementation(ABC):
    @classmethod
    @abstractmethod
    def tool_name(cls) -> str:
        pass

    @property
    @abstractmethod
    def spec(self) -> models.ToolSpec:
        pass

class SyncToolExecutor(ABC):
    @classmethod
    @abstractmethod
    def execute_call(cls, toll_call: models.ToolCall):
        pass

    @classmethod
    @abstractmethod
    def tool_name(cls) -> str:
        pass

class SyncTool(ToolImplementation):
    @abstractmethod
    def call(cls, toll_call: models.ToolCall):
        pass


class AsyncTool(ToolImplementation):
    @abstractmethod
    async def call(cls, toll_call: models.ToolCall):
        pass


class Agent(ABC):
    def __init__(self, spec: models.AgentSpec, tools: list[ToolDefinition] = None):
        self._spec = spec
        if tools is None:
            tools = []
        self._tools = tools

    @classmethod
    @abstractmethod
    def from_spec(cls, spec: models.AgentSpec) -> "Agent":
        pass

    @classmethod
    @abstractmethod
    def _get_tool_type(cls) -> type[ToolDefinition]:
        pass

    def add_tools(self, tools: list[ToolImplementation]) -> Self:
        tooltype = self._get_tool_type()
        return self._add_tools([tooltype.from_implementation(tool) for tool in tools])
    
    def add_tools_from_spec(self, tools: list[models.ToolSpec]) -> Self:
        tooltype = self._get_tool_type()
        return self._add_tools([tooltype.from_spec(tool) for tool in tools])

    @abstractmethod
    def _add_tools(cls, tools: list[ToolDefinition]) -> "Agent":
        pass

    @property
    def spec(self) -> models.AgentSpec:
        return self._spec
    
    @property
    def tools(self) -> list[ToolDefinition]:
        return self._tools


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
