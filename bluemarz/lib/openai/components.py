import json
from time import sleep
from typing import Self

from bluemarz.core.exceptions import InvalidDefinition
from bluemarz.core.interfaces import (
    Agent,
    AssignmentExecutor,
    Session,
    ToolDefinition,
    ToolImplementation,
)
from bluemarz.core.models import (
    AddFileResult,
    AddMessageResult,
    AgentSpec,
    DeleteSessionResult,
    MessageRole,
    RunResult,
    RunResultType,
    SessionFile,
    SessionMessage,
    SessionSpec,
    ToolCall,
    ToolCallResult,
    ToolSpec,
)
from bluemarz.core.registries import ai_agent, ai_session, assignment_executor
from bluemarz.lib.openai import client
from bluemarz.lib.openai.models import (
    FunctionTool,
    OpenAiAssistantSpec,
    OpenAiAssistantToolSpec,
    OpenAiAssistantToolType,
    OpenAiThreadRun,
    OpenAiThreadSpec,
    OpenAiToolCallSpec,
    ThreadMessage,
    ThreadMessageRole,
)

@ai_agent
class OpenAiAssistant(Agent):
    def __init__(
        self,
        api_key: str,
        impl: OpenAiAssistantSpec,
        spec: AgentSpec,
        tools: list["OpenAiAssistantTool"] = None,
    ):
        self._api_key = api_key
        self._impl = impl
        super().__init__(spec, tools)

    @classmethod
    def _get_tool_type(cls) -> "OpenAiAssistantTool":
        return OpenAiAssistantTool

    @classmethod
    def from_spec(cls, spec: AgentSpec) -> "OpenAiAssistant":
        if not spec.id:
            raise ValueError("spec must have id")
        if not spec.id:
            raise ValueError("spec must have api_key")
        
        impl = client.get_assistant(spec.api_key, spec.id)
        if spec.tools:
            tools = [OpenAiAssistantTool.from_spec(t) for t in spec.tools]
        else:
            tools = []

        return cls(spec, spec.api_key, impl, tools)

    @classmethod
    def from_id(cls, api_key: str, assistant_id: str) -> "OpenAiAssistant":
        if not api_key or not assistant_id:
            raise ValueError("api_key and assistant_id are required")

        impl: OpenAiThreadSpec = client.get_assistant(api_key, assistant_id)
        return cls(AgentSpec(id=impl.id), api_key, impl)

    @property
    def tools(self) -> list["OpenAiAssistantTool"]:
        return self._tools

    @property
    def api_key(self) -> str:
        return self._api_key

    @property
    def openai_assistant(self) -> OpenAiAssistantSpec:
        return self._impl

    def _add_tools(self, tools: list[ToolDefinition]) -> Self:
        self._tools.extend([OpenAiAssistantTool.from_definition(t.spec, t.executor) for t in tools])
        return self


@ai_session
class OpenAiAssistantNativeSession(Session):
    def __init__(
        self,
        api_key: str,
        impl: OpenAiThreadSpec,
        spec: SessionSpec,
        files: list[SessionFile] = [],
    ):
        self._api_key = api_key
        self._impl = impl
        self._files = files
        super().__init__(spec)

    @classmethod
    def from_spec(cls, spec: SessionSpec) -> "OpenAiAssistantNativeSession":
        if not spec.api_key:
            raise ValueError("spec must have api_key")
        impl: OpenAiThreadSpec = None
        if spec.id:
            impl = client.get_session(spec.api_key, spec.id)
        else:
            impl = client.create_session(spec.api_key)
            spec.id = impl.id
        return cls(spec.api_key, spec, impl)

    @classmethod
    def from_id(cls, api_key: str, thread_id: str) -> "OpenAiAssistantNativeSession":
        if not api_key or not thread_id:
            raise ValueError("api_key and thread_id are required")

        impl: OpenAiThreadSpec = client.get_session(api_key, thread_id)
        return cls(
            SessionSpec(id=impl.id, type="OpenAiAssistantNativeSession"), api_key, impl
        )

    @classmethod
    def new_session(cls, api_key: str) -> "OpenAiAssistantNativeSession":
        impl: OpenAiThreadSpec = client.create_session(api_key)
        return cls(
            SessionSpec(id=impl.id, type="OpenAiAssistantNativeSession"), api_key, impl
        )

    @property
    def openai_thread(self) -> OpenAiThreadSpec:
        return self._impl

    @property
    def api_key(self) -> str:
        return self._api_key

    @property
    def files(self) -> list[SessionFile]:
        return self._files

    def add_file(self, file: SessionFile) -> AddFileResult:
        raise NotImplementedError

    def add_message(self, message: SessionMessage) -> AddMessageResult:
        role: str = "assistant"
        if message.role == MessageRole.USER:
            role = "user"

        if not message.files:
            client.create_message(self._api_key, self._impl.id, role, message.text)
        else:
            self._files.extend(message.files)
            files = client.upload_files(self._api_key, message.files)
            client.create_message(self._api_key, self._impl.id, role, message.text, files = files)

        return AddMessageResult(ok=True)

    def delete_session(self) -> DeleteSessionResult:
        client.delete_session(self._api_key, self._impl.id)
        return DeleteSessionResult()
    
    def add_tool_call_result(self, tool_call_result: ToolCallResult) -> AddMessageResult:
        text: str = f"Tool called: {tool_call_result.tool_call.tool.name} with arguments {tool_call_result.tool_call.arguments}"

        if tool_call_result.text:
            text += f"\nResult: {tool_call_result.text}"

        if tool_call_result.files:
            text += f"\nResult files: {str([file.file_name for file in tool_call_result.files])[1:-1]}"

        message = SessionMessage(role=MessageRole.SYSTEM, text=text)

        if tool_call_result.files:
            message.files = tool_call_result.files

        self.add_message(message)


def _create_tool_parameters(parameter: ToolSpec.Variable) -> dict:
    type: str = parameter.type.value
    # if not parameter.required:
    #     type = f'["{parameter.type.value}","null"]'

    p = {
        "type": type,
        "description": parameter.description,
    }

    if parameter.type.value == ToolSpec.Variable.VariableType.ENUM:
        p["enum"] = parameter.enum

    return p


class OpenAiAssistantTool(ToolDefinition):
    def __init__(self, impl: OpenAiAssistantToolSpec, spec: ToolSpec, executor: ToolImplementation = None):
        self._impl = impl
        super().__init__(spec, executor)

    @classmethod
    def from_definition(cls, spec: ToolSpec, executor: ToolImplementation = None) -> "OpenAiAssistantTool":
        impl: OpenAiAssistantToolSpec = None
        if spec.variables:
            tool_properties = {
                p[0]: _create_tool_parameters(p[1]) for p in spec.variables.items()
            }

            impl = OpenAiAssistantToolSpec(
                type=OpenAiAssistantToolType.FUNCTION,
                function=FunctionTool(
                    name=spec.name,
                    description=spec.description,
                    parameters={
                        "type": "object",
                        "properties": tool_properties,
                        "additionalProperties": False,
                        "required": [
                            p[0] for p in spec.variables.items() if p[1].required
                        ],
                    },
                    strict=True,
                ),
            )
        else:
            impl = OpenAiAssistantToolSpec(
                type=OpenAiAssistantToolType.FUNCTION,
                function=FunctionTool(
                    name=spec.name,
                    description=spec.description,
                    strict=True,
                ),
            )

        return cls(spec, impl, executor)

    @property
    def openai_tool(self) -> OpenAiAssistantToolSpec:
        return self._impl


def _create_session_message_from_openai_thread_message(
    message: ThreadMessage,
) -> SessionMessage:
    role = MessageRole.AGENT
    if message.role == ThreadMessageRole.USER:
        role = MessageRole.USER

    text: str = None
    if isinstance(message.content, str):
        text = str(message.content)
    else:
        for content in message.content:
            if content.type == "text":
                text = content.text.value

    return SessionMessage(role=role, text=text)


@assignment_executor
class OpenAiAssistantAndThreadExecutor(AssignmentExecutor):
    @staticmethod
    def validate_assignment(
        agent: OpenAiAssistant,
        session: OpenAiAssistantNativeSession,
        run_id: str | None = None,
        **kwargs,
    ) -> None:
        if not agent.api_key == session.api_key:
            raise InvalidDefinition(
                "OpenAi assistant and thread session must have the same api key"
            )

        if run_id:
            try:
                client.get_run(agent.api_key, session.openai_thread.id, run_id)
            except Exception:
                raise InvalidDefinition(f"Could not get executor run with id {run_id}")

    @staticmethod
    def execute(
        agent: OpenAiAssistant,
        session: OpenAiAssistantNativeSession,
        run_id: str | None = None,
        **kwargs,
    ) -> RunResult:
        api_key = agent.api_key
        run: OpenAiThreadRun = None
        if not run_id:
            run = client.create_run(
                api_key,
                session.openai_thread,
                agent.openai_assistant,
                [t.openai_tool for t in agent.tools],
            )
        else:
            run = client.get_run(api_key, session.openai_thread.id, run_id)

        while (
            run.status == "queued"
            or run.status == "in_progress"
            or run.status == "cancelling"
        ):
            sleep(1)
            run = client.get_run(api_key, session.openai_thread.id, run.id)

        result = None
        if run.status == "requires_action":
            tool_calls: list[OpenAiToolCallSpec] = (
                run.required_action.submit_tool_outputs.tool_calls
            )

            tools_dict = {t.spec.name: t.spec for t in agent.tools}

            for tc in tool_calls:
                if tc.function.name not in tools_dict:
                    raise Exception("Agent tried to call unknown tool: ")

            result = RunResult(
                run_id=run.id,
                result_type=RunResultType.TOOL_CALL,
                tool_calls=[
                    ToolCall(
                        id=tc.id,
                        tool=tools_dict[tc.function.name],
                        arguments=json.loads(tc.function.arguments),
                    )
                    for tc in tool_calls
                ],
            )
        elif run.status == "completed":
            messages = client.get_thread_messages(api_key, session.openai_thread.id)

            assistant_messages = []
            for message in messages:
                if message.role == ThreadMessageRole.USER:
                    break

                if message.content and message.content[0].text and message.content[0].text.value.startswith("Tool called: "):
                    break

                assistant_messages.append(message)

            result = RunResult(
                run_id=run.id,
                result_type=RunResultType.MESSAGE_RESPONSE,
                messages=[
                    _create_session_message_from_openai_thread_message(m)
                    for m in reversed(assistant_messages)
                ],
            )
        else:
            raise Exception("Run could not be completed: " + str(run.last_error))

        return result

    @staticmethod
    def submit_tool_calls(
        agent: OpenAiAssistant,
        session: OpenAiAssistantNativeSession,
        run_id: str,
        tc_results: list[ToolCallResult],
        **kwargs,
    ) -> RunResult:
        api_key = agent.api_key

        client.submit_tool_output(
            api_key,
            session.openai_thread.id,
            run_id,
            [
                {"tool_call_id": tcr.tool_call.id, "output": tcr.text}
                for tcr in tc_results
            ],
        )

    @staticmethod
    def prepare_for_async_tool_calls(
        agent: OpenAiAssistant,
        session: OpenAiAssistantNativeSession,
        run_id: str,
        **kwargs,
    ) -> RunResult:
        api_key = agent.api_key

        client.cancel_run(api_key, session.openai_thread.id, run_id)


def init():
    pass
