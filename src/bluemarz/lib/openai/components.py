import json
import logging
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
from bluemarz.core.middleware import apply_api_key_middleware
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
from bluemarz.core.class_registry import ai_agent, ai_session, assignment_executor
from bluemarz.lib.openai import client
from bluemarz.lib.openai.models import (
    FunctionTool,
    OpenAiAssistantSpec,
    OpenAiAssistantToolSpec,
    OpenAiAssistantToolType,
    OpenAiFileSpec,
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
    async def from_spec(cls, spec: AgentSpec) -> "OpenAiAssistant":
        if not spec.id:
            raise ValueError("spec must have id")
        if not spec.api_key:
            raise ValueError("spec must have api_key")

        api_key: str = apply_api_key_middleware(spec.api_key)

        impl = await client.get_assistant(api_key, spec.id)
        if spec.tools:
            tools = [OpenAiAssistantTool.from_spec(t) for t in spec.tools]
        else:
            tools = []

        return cls(api_key, impl, spec, tools)

    @classmethod
    async def from_id(cls, id: str, api_key: str) -> "OpenAiAssistant":
        if not api_key or not id:
            raise ValueError("api_key and assistant_id are required")

        impl: OpenAiThreadSpec = await client.get_assistant(api_key, id)
        return cls(
            api_key,
            impl,
            AgentSpec(id=impl.id, type="OpenAiAssistant", session_type="NativeSession"),
        )

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
        self._tools.extend(
            [OpenAiAssistantTool.from_definition(t.spec, t.executor) for t in tools]
        )
        return self


@ai_session
class OpenAiAssistantNativeSession(Session):
    def __init__(
        self,
        api_key: str,
        impl: OpenAiThreadSpec,
        spec: SessionSpec,
        is_empty: bool = False,
        files: list[SessionFile] = [],
    ):
        self._api_key = api_key
        self._impl = impl
        self._files = files
        self._is_empty = is_empty
        super().__init__(spec)

    @classmethod
    async def from_spec(cls, spec: SessionSpec) -> "OpenAiAssistantNativeSession":
        new_session: bool = not bool(spec.id)

        if not spec.api_key:
            raise ValueError("spec must have api_key")

        api_key: str = apply_api_key_middleware(spec.api_key)

        is_empty: bool = True
        impl: OpenAiThreadSpec = None
        if spec.id:
            impl = await client.get_session(api_key, spec.id)
            is_empty = await check_if_empty_session(api_key, spec.id)
        else:
            impl = await client.create_session(api_key)
            spec.id = impl.id

        session = cls(api_key, impl, spec, is_empty=is_empty)

        if new_session and spec.messages:
            for message in spec.messages:
                await session.add_message(message)

        return session

    @classmethod
    async def from_id(cls, id: str, api_key: str) -> "OpenAiAssistantNativeSession":
        if not api_key or not id:
            raise ValueError("api_key and thread_id are required")

        impl: OpenAiThreadSpec = await client.get_session(api_key, id)
        return cls(
            api_key, impl, SessionSpec(id=impl.id, type="OpenAiAssistantNativeSession")
        )

    @classmethod
    async def new_session(cls, api_key: str) -> "OpenAiAssistantNativeSession":
        impl: OpenAiThreadSpec = await client.create_session(api_key)
        return cls(
            api_key, impl, SessionSpec(id=impl.id, type="OpenAiAssistantNativeSession")
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

    @property
    async def is_empty(self) -> bool:
        return self._is_empty

    async def add_file(self, file: SessionFile) -> AddFileResult:
        openai_files: list[OpenAiFileSpec] = None

        if file.id:
            openai_files = await client.get_files(self._api_key, [file.id])
        else:
            openai_files = await client.upload_files(self._api_key, [file])

        await client.create_message(
            self._api_key, self._impl.id, "user", None, files=openai_files
        )

        if self.is_empty:
            self._is_empty = False

        return AddMessageResult(ok=True)

    async def add_message(self, message: SessionMessage) -> AddMessageResult:
        role: str = "assistant"
        if message.role == MessageRole.USER:
            role = "user"

        if not message.files:
            await client.create_message(
                self._api_key, self._impl.id, role, message.text
            )
        else:
            self._files.extend(message.files)
            files = []

            to_upload = [f for f in message.files if not f.id]
            to_get_ids = [f.id for f in message.files if f.id]

            if to_upload:
                files.extend(await client.upload_files(self._api_key, to_upload))

            if to_get_ids:
                files.extend(await client.get_files(self._api_key, to_get_ids))

            await client.create_message(
                self._api_key, self._impl.id, role, message.text, files=files
            )
        if self.is_empty:
            self._is_empty = False
        return AddMessageResult(ok=True)

    async def delete_session(self) -> DeleteSessionResult:
        await client.delete_session(self._api_key, self._impl.id)
        return DeleteSessionResult()

    async def add_tool_call_result(
        self, tool_call_result: ToolCallResult
    ) -> AddMessageResult:
        # text: str = f"Tool called: {tool_call_result.tool_call.tool.name} with arguments {tool_call_result.tool_call.arguments}"
        text: str = ""

        if tool_call_result.text:
            text += f"{tool_call_result.text}"

        if tool_call_result.files:
            # text += f"\nResult files: {str([file.file_name for file in tool_call_result.files])[1:-1]}"
            text += " "

        message = SessionMessage(role=MessageRole.USER, text=text)

        if tool_call_result.files:
            message.files = tool_call_result.files

        await self.add_message(message)


async def check_if_empty_session(api_key: str, session_id: str) -> bool:
    return not bool(await client.get_thread_messages(api_key, session_id))


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
    def __init__(
        self,
        impl: OpenAiAssistantToolSpec,
        spec: ToolSpec,
        executor: ToolImplementation = None,
    ):
        self._impl = impl
        super().__init__(spec, executor)

    @classmethod
    def from_definition(
        cls, spec: ToolSpec, executor: ToolImplementation = None
    ) -> "OpenAiAssistantTool":
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

        return cls(impl, spec, executor)

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
    async def validate_assignment(
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
                await client.get_run(agent.api_key, session.openai_thread.id, run_id)
            except Exception:
                raise InvalidDefinition(f"Could not get executor run with id {run_id}")

    @staticmethod
    async def execute(
        agent: OpenAiAssistant,
        session: OpenAiAssistantNativeSession,
        run_id: str | None = None,
        **kwargs,
    ) -> RunResult:
        api_key = agent.api_key
        run: OpenAiThreadRun = None
        if not run_id:
            run = await client.create_run(
                api_key,
                session.openai_thread,
                agent.openai_assistant,
                [t.openai_tool for t in agent.tools],
            )
        else:
            run = await client.get_run(api_key, session.openai_thread.id, run_id)

        while (
            run.status == "queued"
            or run.status == "in_progress"
            or run.status == "cancelling"
        ):
            sleep(1)
            run = await client.get_run(api_key, session.openai_thread.id, run.id)

        result = None
        if run.status == "requires_action":
            openai_tool_calls: list[OpenAiToolCallSpec] = (
                run.required_action.submit_tool_outputs.tool_calls
            )

            tools_dict = {t.spec.name: t.spec for t in agent.tools}

            result_tool_calls: list[ToolCall] = []
            for tc in openai_tool_calls:
                if tc.function.name not in tools_dict:
                    logging.warning(
                        f"Agent tried to call tool with no spec: {tc.function.name}"
                    )
                    result_tool_calls.append(
                        ToolCall(
                            id=tc.id,
                            tool_name=tc.function.name,
                            arguments=json.loads(tc.function.arguments),
                        )
                    )
                else:
                    result_tool_calls.append(
                        ToolCall(
                            id=tc.id,
                            tool=tools_dict[tc.function.name],
                            arguments=json.loads(tc.function.arguments),
                        )
                    )

            result = RunResult(
                run_id=run.id,
                result_type=RunResultType.TOOL_CALL,
                tool_calls=result_tool_calls,
            )
        elif run.status == "completed":
            messages = await client.get_thread_messages(
                api_key, session.openai_thread.id
            )

            assistant_messages = []
            for message in messages:
                if message.role == ThreadMessageRole.USER:
                    break

                if (
                    message.content
                    and message.content[0].text
                    and message.content[0].text.value.startswith("Tool called: ")
                ):
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
    async def submit_tool_calls(
        agent: OpenAiAssistant,
        session: OpenAiAssistantNativeSession,
        run_id: str,
        tc_results: list[ToolCallResult],
        **kwargs,
    ) -> RunResult:
        api_key = agent.api_key

        await client.submit_tool_output(
            api_key,
            session.openai_thread.id,
            run_id,
            [
                {"tool_call_id": tcr.tool_call.id, "output": tcr.text}
                for tcr in tc_results
            ],
        )

    @staticmethod
    async def prepare_for_async_tool_calls(
        agent: OpenAiAssistant,
        session: OpenAiAssistantNativeSession,
        run_id: str,
        **kwargs,
    ) -> RunResult:
        api_key = agent.api_key

        await client.cancel_run(api_key, session.openai_thread.id, run_id)


def init():
    pass
