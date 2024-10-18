from enum import Enum
from typing import Any, Self
from pydantic import Field, HttpUrl, model_validator

from bluemarz.utils.model_utils import CamelCaseModel


class AddFileResult(CamelCaseModel):
    ok: bool
    file_id: str = None


class AddMessageResult(CamelCaseModel):
    ok: bool


class DeleteSessionResult(CamelCaseModel):
    ok: bool


class AgentSpec(CamelCaseModel):
    id: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    name: str = Field(None, min_length=1)
    prompt: str = Field(None, min_length=1)
    model: str = Field(None, min_length=1)
    default_query: str | None = Field(None, min_length=1)
    tools: list["ToolSpec"] = []
    parameters: dict[str, Any] = {}


class SessionSpec(CamelCaseModel):
    id: str = Field(None, min_length=1)
    type: str = Field(..., min_length=1)
    messages: list["SessionMessage"] = []
    files: list["SessionFile"] = []
    initial_tool_calls: list["ToolCall"] = []
    parameters: dict[str, Any] = {}


class ToolType(str, Enum):
    SYNC = "sync"
    ASYNC = "async"
    TERMINAL = "terminal"


class ToolSpec(CamelCaseModel):
    class Variable(CamelCaseModel):
        class VariableType(str, Enum):
            STRING = "string"
            NUMBER = "number"
            BOOLEAN = "boolean"
            INTEGER = "integer"
            ENUM = "enum"

        description: str = Field(..., min_length=1)
        type: VariableType
        required: bool = True
        enum: list[str] = None

    tool_type: ToolType
    name: str
    description: str
    variables: dict[str, Variable] = None
    parameters: dict[str, Any] | None = {}


class SessionFile(CamelCaseModel):
    id: str = None
    file_name: str
    file_size_bytes: int
    url: HttpUrl


class ToolCall(CamelCaseModel):
    id: str | None
    tool: ToolSpec
    arguments: dict[str, Any]


class ToolCallResult(CamelCaseModel):
    tool_call: ToolCall
    text: str = None
    files: list[SessionFile] = None
    error: str = None


class MessageRole(str, Enum):
    AGENT = "agent"
    SYSTEM = "system"
    USER = "user"


class SessionMessage(CamelCaseModel):
    role: MessageRole
    text: str | None = Field(None, min_length=1)
    files: list[SessionFile] | None = Field(None, min_length=1)


class RunResultType(str, Enum):
    TOOL_CALL = "toolCall"
    MESSAGE_RESPONSE = "messageResponse"


class RunResult(CamelCaseModel):
    run_id: str
    result_type: RunResultType
    tool_calls: list[ToolCall] = None
    messages: list[SessionMessage] = None

    @model_validator(mode="after")
    def validate_tool(self) -> Self:
        assert (
            self.result_type != RunResultType.TOOL_CALL or len(self.tool_calls) > 0
        )  # Run Result of tool call must have at least one tool call
        return self

    @model_validator(mode="after")
    def validate_message(self) -> Self:
        assert (
            self.result_type != RunResultType.MESSAGE_RESPONSE or len(self.messages) > 0
        )  # Run Result of message response must have at least one message
        return self


class AssignmentRunResult(CamelCaseModel):
    session_id: str
    last_run_result: RunResult
